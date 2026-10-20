"""PID controller implementation with anti-windup."""
import time


class PIDController:
    """Standard PID Controller with clamping and anti-windup."""

    def __init__(self, kp: float, ki: float, kd: float, output_limits: tuple = (-1.0, 1.0)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_out, self.max_out = output_limits

        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_time = None

    def reset(self):
        """Reset PID internal state."""
        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_time = None

    def compute(self, setpoint: float, measured_value: float, current_time: float = None) -> float:
        """Compute PID output given current measurement."""
        if current_time is None:
            current_time = time.time()

        if self._prev_time is None:
            dt = 0.0
        else:
            dt = current_time - self._prev_time

        error = setpoint - measured_value

        p_term = self.kp * error

        # Integral term
        if dt > 0:
            self._integral += error * dt
        i_term = self.ki * self._integral

        # Derivative term
        if dt > 0:
            d_term = self.kd * (error - self._prev_error) / dt
        else:
            d_term = 0.0

        output = p_term + i_term + d_term

        # Clamp output & anti-windup
        clamped_output = max(self.min_out, min(self.max_out, output))
        if output != clamped_output and (output * error > 0):
            # Back-calculate / clamp integral to prevent windup
            if dt > 0 and self.ki != 0:
                self._integral -= error * dt

        self._prev_error = error
        self._prev_time = current_time
        return clamped_output
