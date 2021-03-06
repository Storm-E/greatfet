#
# This file is part of libgreat
#

"""
Module containing the definitions necessary to communicate with libgreat
devices over USB.
"""

from __future__ import absolute_import

import usb
import time
import struct

from ..comms import CommsBackend
from ..errors import DeviceNotFoundError


# Quirk constant that helps us identify libusb's pipe errors, which bubble
# up as generic USBErrors with errno 32 on affected platforms.
LIBUSB_PIPE_ERROR = 32


class USBCommsBackend(CommsBackend):
    """
    Class representing an abstract communications channel used to
    connect with a libgreat board.
    """

    """ The request number for issuing vendor-request encapsulated libgreat commands. """
    LIBGREAT_REQUEST_NUMBER = 0x65


    """ 
    Constant value provided to libgreat vendor requests to indicate that the command
    should execute normally.
    """
    LIBGREAT_VALUE_EXECUTE = 0

    """
    Constant value provided to the libgreat vendor requests indicating that the active
    command should be cancelled.
    """
    LIBGREAT_VALUE_CANCEL = 0xDEAD


    # TODO: handle providing board "URIs", like "usb;serial_number=0x123",
    # and automatic resolution to a backend?

    def __init__(self, **device_identifiers):
        """
        Instantiates a new comms connection to a libgreat device; by default connects
        to the first available board.

        Accepts the same arguments as pyusb's usb.find() method, allowing narrowing
        to a more specific board by serial number.
        """

        # Connect to the first available device.
        try:
            self.device = usb.core.find(**device_identifiers)
        except usb.core.USBError as e:
            # On some platforms, providing identifiers that don't match with any
            # real device produces a USBError/Pipe Error. We'll convert it into a
            # DeviceNotFoundError.
            if e.errno == LIBUSB_PIPE_ERROR:
                raise DeviceNotFoundError()
            else:
                raise e

        # If we couldn't find a board, bail out early.
        if self.device is None:
            raise DeviceNotFoundError()

        # For now, supported boards provide a single configuration, so we
        # can accept the first configuration provided.
        self.device.set_configuration()

        # Run the parent initialization.
        super(USBCommsBackend, self).__init__(**device_identifiers)




    def _vendor_request(self, direction, request, length_or_data=0, value=0, index=0, timeout=1000):
        """Performs a USB vendor-specific control request.

        See also _vendor_request_in()/_vendor_request_out(), which provide a
        simpler syntax for simple requests.

        Args:
            request -- The number of the vendor request to be performed. Usually
                a constant from the protocol.vendor_requests module.
            value -- The value to be passed to the vendor request.

        For IN requests:
            length_or_data -- The length of the data expected in response from the request.
        For OUT requests:
            length_or_data -- The data to be sent to the device.
        """
        return self.device.ctrl_transfer(
            direction | usb.TYPE_VENDOR | usb.RECIP_DEVICE,
            request, value, index, length_or_data, timeout)


    def _vendor_request_in(self, request, length, value=0, index=0, timeout=1000):
        """Performs a USB control request that expects a respnose from the GreatFET.

        Args:
            request -- The number of the vendor request to be performed. Usually
                a constant from the protocol.vendor_requests module.
            length -- The length of the data expected in response from the request.
        """
        return self._vendor_request(usb.ENDPOINT_IN, request, length,
            value=value, index=index, timeout=timeout)


    def _vendor_request_in_string(self, request, length=255, value=0, index=0, timeout=1000,
            encoding='utf-8'):
        """Performs a USB control request that expects a respnose from the GreatFET.

        Interprets the result as an encoded string.

        Args:
            request -- The number of the vendor request to be performed. Usually
                a constant from the protocol.vendor_requests module.
            length -- The length of the data expected in response from the request.
        """
        raw = self._vendor_request(usb.ENDPOINT_IN, request, length_or_data=length,
            value=value, index=index, timeout=timeout)
        return raw.tostring().decode(encoding)


    def _vendor_request_out(self, request, value=0, index=0, data=None, timeout=1000):
        """Performs a USB control request that provides data to the GreatFET.

        Args:
            request -- The number of the vendor request to be performed. Usually
                a constant from the protocol.vendor_requests module.
            value -- The value to be passed to the vendor request.
        """
        return self._vendor_request(usb.ENDPOINT_OUT, request, value=value,
            index=index, length_or_data=data, timeout=timeout)


    @staticmethod
    def _build_command_prelude(class_number, verb):
        """Builds a libgreat command prelude, which identifies the command
        being executed to libgreat.
        """
        return struct.pack("<II", class_number, verb)


    def _usb_serial_number(self):
        """ Reports the device's USB serial number. """
        return self.device.serial_number


    def execute_raw_command(self, class_number, verb, data=None, timeout=1000,
            encoding=None, max_response_length=4096, comms_timeout=1000):
        """Executes a libgreat command.

        Args:
            class_number -- The class number for the given command.
                See the GreatFET wiki for a list of class numbers.
            verb -- The verb number for the given command.
                See the GreatFET wiki for the given class.
            data -- Data to be transmitted to the GreatFET.
            timeout -- Maximum command execution time, in ms.
            encoding -- If specified, the response data will attempt to be
                decoded in the provided format.
            max_response_length -- If less than 4096, this parameter will
                cut off the provided response at the given length.

        Returns any data recieved in response.
        """

        # Build the command header, which identifies the command to be executed.
        prelude = self._build_command_prelude(class_number, verb)

        # If we have data, build it into our request.
        if data:
            to_send = prelude + bytearray(data)

            if len(to_send) > self.LIBGREAT_MAX_COMMAND_SIZE:
                raise ArgumentError("Command payload is too long!")

        # Otherwise, just send the prelude.
        else:
            to_send = prelude

        # Send the command (including prelude) to the device...
        # TODO: upgrade this to be able to not block?
        try:
            self.device.ctrl_transfer(
                usb.ENDPOINT_OUT | usb.TYPE_VENDOR | usb.RECIP_ENDPOINT,
                self.LIBGREAT_REQUEST_NUMBER, self.LIBGREAT_VALUE_EXECUTE, 0, to_send, timeout)

            # Truncate our maximum, if necessary.
            if max_response_length > 4096:
                max_response_length = self.LIBGREAT_MAX_COMMAND_SIZE

            # ... and read any response the device has prepared for us.
            # TODO: use our own timeout, rather than the command timeout, to
            # avoid doubling the overall timeout
            response = self.device.ctrl_transfer(
                usb.ENDPOINT_IN | usb.TYPE_VENDOR | usb.RECIP_ENDPOINT,
                self.LIBGREAT_REQUEST_NUMBER, self.LIBGREAT_VALUE_EXECUTE, 0, max_response_length, comms_timeout)

            # If we were passed an encoding, attempt to decode the response data.
            if encoding and response:
                response = response.tostring().decode(encoding)

            # Return the device's response.
            return response

        except:
            self.abort_command()
            raise


    def abort_command(self, timeout=1000, retry_delay=1):
        """ Aborts execution of a current libgreat command. Used for error handling.  """

        # FIXME: these should be moved to a backend module in the libgreat
        # host library
        LIBGREAT_REQUEST_NUMBER = 0x65

        # Create a quick function to issue the abort request.
        execute_abort = lambda device : device.ctrl_transfer(
                usb.ENDPOINT_OUT | usb.TYPE_VENDOR | usb.RECIP_ENDPOINT,
                self.LIBGREAT_REQUEST_NUMBER, self.LIBGREAT_VALUE_CANCEL, 0, None, timeout)

        # And try executing the abort progressively, mutiple times.
        try:
            execute_abort(self.device)
        except:
            if retry_delay:
                time.sleep(retry_delay)
                execute_abort(self.device)
            else:
                raise


    def close(self):
        """
        Dispose resources allocated by this connection.  This connection
        will no longer be usable.
        """
        usb.util.dispose_resources(self.device)

