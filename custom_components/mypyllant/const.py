DOMAIN = "mypyllant"
OPTION_UPDATE_INTERVAL = "update_interval"
OPTION_UPDATE_INTERVAL_DAILY = "update_interval_daily"
OPTION_REFRESH_DELAY = "refresh_delay"
OPTION_DEFAULT_QUICK_VETO_DURATION = "quick_veto_duration"
OPTION_DEFAULT_HOLIDAY_DURATION = "holiday_duration"
OPTION_COUNTRY = "country"
OPTION_BRAND = "brand"
OPTION_TIME_PROGRAM_OVERWRITE = "time_program_overwrite"
OPTION_DEFAULT_HOLIDAY_SETPOINT = "default_holiday_setpoint"
OPTION_FETCH_RTS = "fetch_rts"
OPTION_FETCH_MPC = "fetch_mpc"
OPTION_FETCH_AMBISENSE_ROOMS = "fetch_ambisense_rooms"
DEFAULT_UPDATE_INTERVAL = 60  # in seconds
DEFAULT_UPDATE_INTERVAL_DAILY = 3600  # in seconds
DEFAULT_REFRESH_DELAY = 5  # in seconds
DEFAULT_COUNTRY = "germany"
DEFAULT_TIME_PROGRAM_OVERWRITE = False
DEFAULT_HOLIDAY_SETPOINT = 10.0  # in °C
DEFAULT_FETCH_RTS = False
DEFAULT_FETCH_MPC = False
DEFAULT_FETCH_AMBISENSE_ROOMS = True
QUOTA_PAUSE_INTERVAL = 3 * 3600  # in seconds
API_DOWN_PAUSE_INTERVAL = 15 * 60  # in seconds

SERVICE_SET_QUICK_VETO = "set_quick_veto"
SERVICE_SET_MANUAL_MODE_SETPOINT = "set_manual_mode_setpoint"
SERVICE_CANCEL_QUICK_VETO = "cancel_quick_veto"
SERVICE_SET_HOLIDAY = "set_holiday"
SERVICE_CANCEL_HOLIDAY = "cancel_holiday"
SERVICE_SET_TIME_PROGRAM = "set_time_program"
SERVICE_SET_ZONE_TIME_PROGRAM = "set_zone_time_program"
SERVICE_SET_ZONE_OPERATING_MODE = "set_zone_operating_mode"
SERVICE_SET_ZONE_TIME_PROGRAM_TEMPERATURE = "set_zone_time_program_temperature"
SERVICE_SET_DHW_TIME_PROGRAM = "set_dhw_time_program"
SERVICE_SET_DHW_CIRCULATION_TIME_PROGRAM = "set_dhw_circulation_time_program"
SERVICE_SET_VENTILATION_FAN_STAGE = "set_ventilation_fan_stage"
SERVICE_EXPORT = "export"
SERVICE_GENERATE_TEST_DATA = "generate_test_data"
SERVICE_REPORT = "report"

WEEKDAYS_TO_RFC5545 = {
    "monday": "MO",
    "tuesday": "TU",
    "wednesday": "WE",
    "thursday": "TH",
    "friday": "FR",
    "saturday": "SA",
    "sunday": "SU",
}
RFC5545_TO_WEEKDAYS = {v: k for k, v in WEEKDAYS_TO_RFC5545.items()}
