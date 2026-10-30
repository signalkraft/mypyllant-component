from datetime import datetime, timedelta, timezone
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from myPyllant.api import MyPyllantAPI
from myPyllant.models import DeviceData, DeviceDataBucket
from myPyllant.tests.utils import list_test_data

from custom_components.mypyllant.const import STATISTICS_BACKFILL_MAX_DAYS
from custom_components.mypyllant.coordinator import (
    DailyDataCoordinator,
    backfill_ranges,
    local_midnight,
    merge_device_data,
)

TZ = ZoneInfo("Europe/Berlin")
START = datetime(2026, 10, 29, tzinfo=TZ)


def _bucket(start: datetime, value: float) -> DeviceDataBucket:
    return DeviceDataBucket(
        start_date=start, end_date=start + timedelta(hours=1), value=value
    )


def _device_data(buckets, operation_mode="HEATING") -> DeviceData:
    return DeviceData(
        operation_mode=operation_mode,
        energy_type="CONSUMED_PRIMARY_ENERGY",
        data=buckets,
    )


def test_backfill_ranges_respects_max_days():
    ranges = backfill_ranges(START - timedelta(days=5), START, 2)
    assert ranges == [
        (START - timedelta(days=5), START - timedelta(days=3)),
        (START - timedelta(days=3), START - timedelta(days=1)),
        (START - timedelta(days=1), START),
    ]
    assert backfill_ranges(START, START, 2) == []


def test_local_midnight_across_dst():
    # 2026-10-25 is the DST change in Europe/Berlin
    value = datetime(2026, 10, 25, 15, tzinfo=TZ)
    assert local_midnight(value, TZ) == datetime(2026, 10, 25, tzinfo=TZ)
    assert local_midnight(value.astimezone(timezone.utc), TZ).hour == 0


def test_merge_device_data_prepends_earlier_buckets():
    early = START - timedelta(hours=2)
    current = [_device_data([_bucket(START, 300.0)])]
    earlier = [
        _device_data([_bucket(early, 100.0), _bucket(START, 999.0)]),
    ]
    merge_device_data(current, earlier)
    assert [b.start_date for b in current[0].data] == [early, START]
    # overlap keeps the value of the newer (regular) fetch
    assert current[0].data[1].value == 300.0


def test_merge_device_data_ignores_other_series():
    current = [_device_data([_bucket(START, 300.0)], "HEATING")]
    merge_device_data(
        current,
        [
            _device_data(
                [_bucket(START - timedelta(hours=1), 1.0)], "DOMESTIC_HOT_WATER"
            )
        ],
    )
    assert len(current[0].data) == 1


def _coordinator(hass, last_starts: dict[int, datetime | None]):
    coordinator = DailyDataCoordinator.__new__(DailyDataCoordinator)
    coordinator.hass = hass
    hass.config.components.add("recorder")
    device = MagicMock()
    device.system_id = "system"
    device.device_uuid = "uuid"
    device.data = [MagicMock(skip_data_update=False) for _ in last_starts]

    async def fake_job(func, hass, number, statistic_id, *rest):
        da_index = int(statistic_id.split("_")[-2])
        last = last_starts[da_index]
        return {statistic_id: [{"start": last.timestamp()}]} if last else {}

    patcher = patch("custom_components.mypyllant.coordinator.get_instance")
    mock_recorder = patcher.start()
    mock_recorder.return_value.async_add_executor_job = AsyncMock(side_effect=fake_job)
    return coordinator, device, patcher


async def test_statistics_gap_start_uses_oldest_series(hass):
    coordinator, device, patcher = _coordinator(
        hass,
        {
            0: START - timedelta(days=2, hours=-5),  # 27.10. 05:00
            1: START + timedelta(hours=8),  # up to date
        },
    )
    try:
        gap = await coordinator.statistics_gap_start(device, 0, START, TZ)
    finally:
        patcher.stop()
    assert gap == datetime(2026, 10, 27, tzinfo=TZ)


async def test_statistics_gap_start_is_capped(hass):
    coordinator, device, patcher = _coordinator(hass, {0: START - timedelta(days=30)})
    try:
        gap = await coordinator.statistics_gap_start(device, 0, START, TZ)
    finally:
        patcher.stop()
    assert gap == START - timedelta(days=STATISTICS_BACKFILL_MAX_DAYS)


async def test_statistics_gap_start_none_when_up_to_date_or_new(hass):
    coordinator, device, patcher = _coordinator(
        hass, {0: START + timedelta(hours=3), 1: None}
    )
    try:
        assert await coordinator.statistics_gap_start(device, 0, START, TZ) is None
    finally:
        patcher.stop()

    coordinator, device, patcher = _coordinator(hass, {0: None})
    try:
        assert await coordinator.statistics_gap_start(device, 0, START, TZ) is None
    finally:
        patcher.stop()


@pytest.mark.parametrize("test_data", list_test_data(only_with_systems=True))
async def test_daily_data_fetches_gap_in_chunks(
    mypyllant_aioresponses,
    mocked_api: MyPyllantAPI,
    daily_data_coordinator_mock,
    test_data,
):
    with mypyllant_aioresponses(test_data) as _:
        system_coordinator = daily_data_coordinator_mock.hass_data["system_coordinator"]
        system_coordinator.data = await system_coordinator._async_update_data()
        if not any(s.devices for s in system_coordinator.data or []):
            await mocked_api.aiohttp_session.close()
            pytest.skip("No devices in test data")

        calls = []
        original = mocked_api.get_data_by_device

        def spy(device, resolution, start, end):
            calls.append((start, end))
            return original(device, resolution, start, end)

        async def gap(device, de_index, start, tz):
            return start - timedelta(days=3)

        with (
            mock.patch.object(mocked_api, "get_data_by_device", side_effect=spy),
            mock.patch.object(
                DailyDataCoordinator, "statistics_gap_start", side_effect=gap
            ),
        ):
            await daily_data_coordinator_mock._async_update_data()

        devices = sum(len(s.devices) for s in system_coordinator.data)
        # regular yesterday+today fetch plus two backfill chunks (2 + 1 days) per device
        assert len(calls) == devices * 3
        regular_start = calls[0][0]
        assert calls[1] == (
            regular_start - timedelta(days=3),
            regular_start - timedelta(days=1),
        )
        assert calls[2] == (regular_start - timedelta(days=1), regular_start)
        await mocked_api.aiohttp_session.close()
