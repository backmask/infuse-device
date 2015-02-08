import logging
logger = logging.getLogger(__name__)

from .radiodriver import RadioDriver
from .udpdriver import UdpDriver
from .serialdriver import SerialDriver
from .debugdriver import DebugDriver
from .usbdriver import UsbDriver
from .exceptions import WrongUriType

DRIVERS = [RadioDriver, SerialDriver, UdpDriver, DebugDriver, UsbDriver]
INSTANCES = []

class Crtp:

    @staticmethod
    def init_drivers(enable_debug_driver=False):
        """Initialize all the drivers."""
        for driver in DRIVERS:
            try:
                if driver != DebugDriver or enable_debug_driver:
                    INSTANCES.append(driver())
            except Exception:  # pylint: disable=W0703
                continue

    @staticmethod
    def scan_interfaces():
        """ Scan all the interfaces for available Crazyflies """
        available = []
        found = []
        for instance in INSTANCES:
            logger.debug("Scanning: %s", instance)
            try:
                found = instance.scan_interface()
                available += found
            except Exception:
                raise
        return available

    @staticmethod
    def get_interfaces_status():
        """Get the status of all the interfaces"""
        status = {}
        for instance in INSTANCES:
            try:
                status[instance.get_name()] = instance.get_status()
            except Exception:
                raise
        return status

    @staticmethod
    def get_link_driver(uri, link_quality_callback=None, link_error_callback=None):
        """Return the link driver for the given URI. Returns None if no driver
        was found for the URI or the URI was not well formatted for the matching
        driver."""
        for instance in INSTANCES:
            try:
                instance.connect(uri, link_quality_callback, link_error_callback)
                return instance
            except WrongUriType:
                continue

        return None
