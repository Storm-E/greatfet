#
# This file is part of GreatFET
#

cmake_minimum_required(VERSION 3.1.3)
set(CMAKE_TOOLCHAIN_FILE ../cmake/toolchain-arm-cortex-m.cmake)

project(greatfet_usb)

include(../cmake/greatfet-common.cmake)

# Automatically include all GreatFET API classes.
# This enables us to simply add a file to the 'classes' directory to add a new
# communications API class.
AUX_SOURCE_DIRECTORY(classes GREATFET_API_CLASSES) 
AUX_SOURCE_DIRECTORY("${LIBGREAT_FIRMWARE_COMMON}/classes" LIBGREAT_API_CLASSES)

set(SRC_M4
    greatfet_usb.c
    usb_request_handlers.c
    usb_bulk_buffer.c
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/usb/${LIBGREAT_PLATFORM}/usb.c"
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/usb/${LIBGREAT_PLATFORM}/usb_host.c"
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/usb/${LIBGREAT_PLATFORM}/usb_request.c"
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/usb/${LIBGREAT_PLATFORM}/usb_standard_request.c"
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/usb/${LIBGREAT_PLATFORM}/usb_queue.c"
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/usb/${LIBGREAT_PLATFORM}/usb_queue_host.c"
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/usb/comms_backend.c"
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/comms/comms_class.c"
    "${PATH_LIBGREAT_FIRMWARE_DRIVERS}/comms/utils.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/gpdma.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/gpio_dma.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/gpio_scu.c"
    usb_descriptor.c
    usb_device.c
    usb_endpoint.c
    sgpio_isr.c
    "${PATH_GREATFET_FIRMWARE_COMMON}/glitchkit.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/fault_handler.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/rom_iap.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/spi_bus.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/debug.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/printf.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/sgpio.c"
    "${PATH_GREATFET_FIRMWARE_COMMON}/one_wire.c"

    ${LIBGREAT_API_CLASSES}
    ${GREATFET_API_CLASSES}

    # TODO: get rid of these!
    usb_api_spi.c
    usb_api_adc.c
    usb_api_dac.c
    usb_api_i2c.c
    usb_api_gpio.c
    usb_api_leds.c
    usb_api_logic_analyzer.c
    usb_api_sdir.c
    usb_api_greatdancer.c
    usb_api_usbhost.c
    usb_api_glitchkit.c
    usb_api_glitchkit_simple.c
    usb_api_glitchkit_usb.c
    usb_api_DS18B20.c
    usb_api_msp430.c
)

DeclareTargets()
