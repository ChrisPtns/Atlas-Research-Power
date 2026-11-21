#!/usr/bin/env python3
import math as m, rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy as RelP, HistoryPolicy as HistP
from geometry_msgs.msg import Twist
from sensor_msgs.msg import NavSatFix, Imu
from std_msgs.msg import Float64MultiArray, String

w_pi = lambda a: m.atan2(m.sin(a), m.cos(a))


class PathNode(Node):
    def __init__(self):
        super().__init__("atlas_path_planner")
        for k, v in (
            ("loop_rate_hz", 20.0),
            ("max_surge_vel", 0.85),
            ("min_surge_ratio", 0.15),
            ("max_yaw_rate", 0.80),
            ("kp_yaw", 1.40),
            ("kd_yaw", 0.25),
            ("ki_cross_track", 0.05),
            ("lookahead_min_m", 2.0),
            ("lookahead_max_m", 6.0),
            ("lookahead_gamma", 0.45),
            ("acceptance_radius_m", 2.5),
            ("slowdown_radius_m", 5.0),
            ("loop_mission", False),
            ("default_waypoints_enu", [0.0, 0.0, 20.0, 0.0, 20.0, 15.0, 0.0, 15.0]),
        ):
            self.declare_parameter(k, v)
        g = lambda k: self.get_parameter(k).value
        self.hz, self.v_mx, self.v_mn, self.w_mx = (
            g("loop_rate_hz"),
            g("max_surge_vel"),
            g("min_surge_ratio"),
            g("max_yaw_rate"),
        )
        self.kp, self.kd, self.ki, self.la_mn, self.la_mx, self.gam = (
            g("kp_yaw"),
            g("kd_yaw"),
            g("ki_cross_track"),
            g("lookahead_min_m"),
            g("lookahead_max_m"),
            g("lookahead_gamma"),
        )
        self.r_ac, self.r_sl, self.lp_w, raw_w = (
            g("acceptance_radius_m"),
            g("slowdown_radius_m"),
            g("loop_mission"),
            g("default_waypoints_enu"),
        )
        self.wps = [
            (float(raw_w[i]), float(raw_w[i + 1])) for i in range(0, len(raw_w) - 1, 2)
        ]
        self.wp_i, self.done, self.lat0, self.lon0 = (
            (1 if len(self.wps) > 1 else 0),
            False,
            None,
            None,
        )
        self.px, self.py, self.psi, self.r_z, self.ct_i, self.v_st = (
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            "IDLE_DISARMED",
        )
        q_f = QoSProfile(reliability=RelP.BEST_EFFORT, history=HistP.KEEP_LAST, depth=1)
        q_r = QoSProfile(reliability=RelP.RELIABLE, history=HistP.KEEP_LAST, depth=10)
        for t, tp, cb, q in (
            (NavSatFix, "/gps/fix", self.cb_gps, q_f),
            (Imu, "/imu/data", self.cb_imu, q_f),
            (Float64MultiArray, "/mission/waypoints_enu", self.cb_wp, q_r),
            (String, "/vessel/state", self.cb_st, q_r),
        ):
            self.create_subscription(t, tp, cb, q)
        self.p_aut, self.p_rth = self.create_publisher(
            Twist, "/cmd_vel/auto", q_f
        ), self.create_publisher(Twist, "/cmd_vel/rth", q_f)
        self.tmr = self.create_timer(1.0 / self.hz, self.step_nav)

    def cb_gps(self, msg):
        if msg.status.status < 0:
            return
        if self.lat0 is None:
            self.lat0, self.lon0 = msg.latitude, msg.longitude
        self.px = (
            6378137.0
            * m.radians(msg.longitude - self.lon0)
            * m.cos(m.radians(self.lat0))
        )
        self.py = 6378137.0 * m.radians(msg.latitude - self.lat0)

    def cb_imu(self, msg):
        q = msg.orientation
        self.psi = m.atan2(
            2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )
        self.r_z = msg.angular_velocity.z

    def cb_wp(self, msg):
        d = msg.data
        if len(d) >= 2:
            self.wps = [(self.px, self.py)] + [
                (float(d[i]), float(d[i + 1])) for i in range(0, len(d) - 1, 2)
            ]
            self.wp_i, self.done, self.ct_i = 1, False, 0.0

    def cb_st(self, msg):
        self.v_st = msg.data
        if self.v_st != "AUTONOMOUS_SURVEY":
            self.ct_i = 0.0

    def step_nav(self):
        self.p_aut.publish(self.calc_alos())
        self.p_rth.publish(self.calc_homing(0.0, 0.0))

    def calc_alos(self):
        if self.done or len(self.wps) < 2:
            return Twist()
        x0, y0 = self.wps[self.wp_i - 1]
        x1, y1 = self.wps[self.wp_i]
        dx, dy = x1 - x0, y1 - y0
        s_len = m.hypot(dx, dy)
        a_k = m.atan2(dy, dx) if s_len > 1e-3 else 0.0
        rx, ry = self.px - x0, self.py - y0
        s_at = rx * m.cos(a_k) + ry * m.sin(a_k)
        e_ct = -rx * m.sin(a_k) + ry * m.cos(a_k)
        d_wp = m.hypot(x1 - self.px, y1 - self.py)
        if d_wp <= self.r_ac or (s_len > 1e-3 and s_at >= s_len):
            self.ct_i = 0.0
            if self.wp_i < len(self.wps) - 1:
                self.wp_i += 1
            elif self.lp_w:
                self.wps.append(self.wps[1])
                self.wp_i += 1
            else:
                self.done = True
                return Twist()
        d_la = self.la_mn + (self.la_mx - self.la_mn) * m.exp(-self.gam * abs(e_ct))
        den = d_la**2 + (e_ct + self.ki * self.ct_i) ** 2
        self.ct_i = max(
            -10.0,
            min(10.0, self.ct_i + (1.0 / self.hz) * (d_la * e_ct) / max(den, 1e-3)),
        )
        chi_d = w_pi(a_k + m.atan2(-(e_ct + self.ki * self.ct_i), d_la))
        return self.trk_vel(chi_d, d_wp)

    def calc_homing(self, tx, ty):
        d = m.hypot(tx - self.px, ty - self.py)
        return (
            Twist()
            if d <= self.r_ac
            else self.trk_vel(m.atan2(ty - self.py, tx - self.px), d)
        )

    def trk_vel(self, chi_d, d_goal):
        out = Twist()
        e_psi = w_pi(chi_d - self.psi)
        out.angular.z = max(
            -self.w_mx, min(self.w_mx, (self.kp * e_psi) - (self.kd * self.r_z))
        )
        out.linear.x = (
            self.v_mx
            * max(self.v_mn, m.cos(e_psi))
            * m.tanh(d_goal / max(self.r_sl, 0.5))
        )
        return out


def main(args=None):
    rclpy.init(args=args)
    nd = PathNode()
    try:
        rclpy.spin(nd)
    except KeyboardInterrupt:
        pass
    finally:
        nd.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
