#!/usr/bin/env python3
from enum import IntEnum, auto
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy as RelPol,
    HistoryPolicy as HistPol,
    DurabilityPolicy as DurPol,
)
from std_msgs.msg import String, Float32, Bool, Empty
from geometry_msgs.msg import Twist


class VState(IntEnum):
    IDLE_DISARMED = auto()
    MANUAL_RC = auto()
    AUTONOMOUS_SURVEY = auto()
    SHALLOW_AVOIDANCE = auto()
    FAILSAFE_RTH = auto()
    EMERGENCY_STOP = auto()


class FSMNode(Node):
    def __init__(self):
        super().__init__("atlas_state_machine")
        for k, v in (
            ("loop_rate_hz", 20.0),
            ("lora_timeout_sec", 30.0),
            ("min_battery_voltage", 13.4),
            ("min_safe_depth_m", 0.50),
            ("clear_safe_depth_m", 0.70),
            ("debounce_ticks", 10),
            ("mission_profile", "PROFILE_A"),
        ):
            self.declare_parameter(k, v)
        g_p = lambda p: self.get_parameter(p).value
        self.hz, self.to_lora, self.min_v, self.min_d, self.clr_d, self.db_t = (
            g_p("loop_rate_hz"),
            g_p("lora_timeout_sec"),
            g_p("min_battery_voltage"),
            g_p("min_safe_depth_m"),
            g_p("clear_safe_depth_m"),
            g_p("debounce_ticks"),
        )
        self.st = self.req = VState.IDLE_DISARMED
        self.t_hb = self.get_clock().now()
        self.cur_v, self.cur_d, self.kill, self.cnt_v, self.cnt_d = (
            16.8,
            10.0,
            False,
            0,
            0,
        )
        self.v_man, self.v_aut, self.v_rth = Twist(), Twist(), Twist()
        q_sns = QoSProfile(
            reliability=RelPol.BEST_EFFORT, history=HistPol.KEEP_LAST, depth=1
        )
        q_rel = QoSProfile(
            reliability=RelPol.RELIABLE,
            durability=DurPol.TRANSIENT_LOCAL,
            history=HistPol.KEEP_LAST,
            depth=10,
        )
        for t, m, c, q in (
            (Empty, "/telemetry/heartbeat", self.cb_hb, q_sns),
            (Float32, "/power/voltage", self.cb_vlt, q_sns),
            (Float32, "/sonar/depth", self.cb_dep, q_sns),
            (Bool, "/safety/kill_switch", self.cb_kil, q_rel),
            (String, "/gcs/mode_request", self.cb_req, q_rel),
            (Twist, "/cmd_vel/manual", self.cb_man, q_sns),
            (Twist, "/cmd_vel/auto", self.cb_aut, q_sns),
            (Twist, "/cmd_vel/rth", self.cb_rth, q_sns),
        ):
            self.create_subscription(t, m, c, q)
        self.p_st, self.p_vel = self.create_publisher(
            String, "/vessel/state", q_rel
        ), self.create_publisher(Twist, "/cmd_vel/out", q_sns)
        self.tmr = self.create_timer(1.0 / self.hz, self.step_run)

    def cb_hb(self, _):
        self.t_hb = self.get_clock().now()

    def cb_vlt(self, msg):
        self.cur_v = msg.data

    def cb_dep(self, msg):
        self.cur_d = msg.data

    def cb_kil(self, msg):
        self.kill = msg.data

    def cb_req(self, msg):
        req_s = msg.data.upper()
        if req_s in VState.__members__:
            self.req = VState[req_s]

    def cb_man(self, msg):
        self.v_man = msg

    def cb_aut(self, msg):
        self.v_aut = msg

    def cb_rth(self, msg):
        self.v_rth = msg

    def step_run(self):
        nxt = self.eval_st()
        if nxt != self.st:
            self.st = nxt
            m = String()
            m.data = self.st.name
            self.p_st.publish(m)
        self.mux_out()

    def eval_st(self):
        if self.kill:
            return VState.EMERGENCY_STOP
        if self.req == VState.IDLE_DISARMED:
            return VState.IDLE_DISARMED
        self.cnt_v = self.cnt_v + 1 if self.cur_v < self.min_v else 0
        self.cnt_d = (
            self.cnt_d + 1
            if self.cur_d < self.min_d
            else (0 if self.cur_d >= self.clr_d else self.cnt_d)
        )
        lora_err = (
            (self.get_clock().now() - self.t_hb).nanoseconds * 1e-9
        ) > self.to_lora
        if lora_err or (self.cnt_v >= self.db_t):
            return (
                VState.MANUAL_RC
                if (not lora_err and self.req == VState.MANUAL_RC)
                else VState.FAILSAFE_RTH
            )
        if self.st == VState.AUTONOMOUS_SURVEY and self.cnt_d >= 3:
            return VState.SHALLOW_AVOIDANCE
        if self.st == VState.SHALLOW_AVOIDANCE:
            return (
                VState.AUTONOMOUS_SURVEY
                if self.cnt_d == 0
                else (
                    VState.MANUAL_RC
                    if self.req == VState.MANUAL_RC
                    else VState.SHALLOW_AVOIDANCE
                )
            )
        return (
            self.req
            if self.req in (VState.MANUAL_RC, VState.AUTONOMOUS_SURVEY)
            else self.st
        )

    def mux_out(self):
        out_t = Twist()
        if self.st == VState.MANUAL_RC:
            out_t = self.v_man
        elif self.st == VState.AUTONOMOUS_SURVEY:
            out_t = self.v_aut
        elif self.st == VState.FAILSAFE_RTH:
            out_t = self.v_rth
        elif self.st == VState.SHALLOW_AVOIDANCE:
            out_t.linear.x, out_t.angular.z = -0.35, 0.40
        self.p_vel.publish(out_t)


def main(args=None):
    rclpy.init(args=args)
    nd = FSMNode()
    try:
        rclpy.spin(nd)
    except KeyboardInterrupt:
        pass
    finally:
        nd.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
