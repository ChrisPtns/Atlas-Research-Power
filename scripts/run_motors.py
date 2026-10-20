#!/usr/bin/env python3
"""Run and test motors with safety watchdog."""
import logging
import time
from src.hardware.pca9685_driver import PCA9685Driver
from src.safety.watchdog import Watchdog

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_motors")


def emergency_stop():
    logger.error("WATCHDOG TIMEOUT! Motors stopped immediately.")


def main():
    logger.info("Initializing motor runner...")
    driver = PCA9685Driver()
    watchdog = Watchdog(timeout_sec=0.5, on_timeout=emergency_stop)
    watchdog.start()

    try:
        for i in range(5):
            watchdog.kick()
            logger.info("Motors spinning - Step %d/5", i + 1)
            driver.set_pwm(0, 1600)
            time.sleep(0.1)
    finally:
        watchdog.stop()
        driver.set_pwm(0, 1500)
        logger.info("Motor sequence completed.")


if __name__ == "__main__":
    main()
