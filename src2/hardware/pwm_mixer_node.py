#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy as RelP, HistoryPolicy as HistP
from geometry_msgs.msg import Twist
from std_msgs.msg import Int16MultiArray


class MixNode(Node):
    def __init__(self):
        super().__init__("atlas_pwm_mixer")
        for k, v in (
            ("hull_track_width_m", 0.49),
            ("neutral_pulse_us", 1500),
            ("max_delta_pulse_us", 400),
        ):
            self.declare_parameter(k, v)
        p = lambda k: self.get_parameter(k).value
        self.tr_w, self.mid, self.max_d = (
            p("hull_track_width_m"),
            p("neutral_pulse_us"),
            p("max_delta_pulse_us"),
        )
        q_fst = QoSProfile(
            reliability=RelP.BEST_EFFORT, history=HistP.KEEP_LAST, depth=1
        )
        self.create_subscription(Twist, "/cmd_vel/out", self.cb_vel, q_fst)
        self.pub_pwm = self.create_publisher(
            Int16MultiArray, "/hardware/esc_pwm_us", q_fst
        )

    def cb_vel(self, msg):
        v_x, v_z = msg.linear.x, msg.angular.z
        e_l, e_r = v_x - (v_z * self.tr_w * 0.5), v_x + (v_z * self.tr_w * 0.5)
        mag = max(abs(e_l), abs(e_r), 1.0)
        msg_out = Int16MultiArray()
        msg_out.data = [
            int(self.mid + (e_l / mag) * self.max_d),
            int(self.mid + (e_r / mag) * self.max_d),
        ]
        self.pub_pwm.publish(msg_out)


def main(args=None):
    rclpy.init(args=args)
    nd = MixNode()
    try:
        rclpy.spin(nd)
    except KeyboardInterrupt:
        pass
    finally:
        nd.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
