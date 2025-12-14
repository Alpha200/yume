"""
Integration tests for EFA VRR API (Verkehrsverbund Rhein-Ruhr)

This test uses the public EFA API from VRR (https://efa.vrr.de/standard/)
No authentication required, but tests real API calls.

Run with: python -m pytest tests/test_efa_vrr.py -v -s
"""

import pytest

import services.efa as efa_module
from services.efa import (
    get_station_id,
    get_departures,
    get_departures_json,
    get_serving_lines,
    find_line_id,
    efa_request,
    _parse_departure_time,
    _calculate_delay,
    PublicTransportDeparture,
    get_journeys
)


# VRR API endpoint for testing
VRR_API_URL = "https://efa.vrr.de/standard"


@pytest.fixture
def vrr_env():
    """Set up VRR environment variables for testing"""
    # Patch the module variables directly since they're loaded at import time
    original_url = efa_module.EFA_API_URL
    original_client_id = efa_module.EFA_CLIENT_ID
    original_client_name = efa_module.EFA_CLIENT_NAME
    
    efa_module.EFA_API_URL = VRR_API_URL
    efa_module.EFA_CLIENT_ID = "TESTCLIENT"
    efa_module.EFA_CLIENT_NAME = "pytest"
    
    yield
    
    # Restore original values
    efa_module.EFA_API_URL = original_url
    efa_module.EFA_CLIENT_ID = original_client_id
    efa_module.EFA_CLIENT_NAME = original_client_name


class TestEFARequestFunction:
    """Test the generic EFA request function"""
    
    @pytest.mark.asyncio
    async def test_efa_request_with_valid_params(self, vrr_env):
        """Test making a valid request to EFA API"""
        result = await efa_request(
            "/location.do",
            params={"name": "Essen Hauptbahnhof", "type": "STOP"}
        )
        
        assert result["status"] in [200, 400, 404], f"Unexpected status: {result['status']}"
        assert "data" in result


class TestStationLookup:
    """Test station lookup functionality"""
    
    @pytest.mark.asyncio
    async def test_find_major_station_essen(self, vrr_env):
        """Test finding a major station (Essen Hauptbahnhof)"""
        station_id = await get_station_id("Essen Hauptbahnhof")
        
        # Essen Hauptbahnhof should be found
        assert station_id is not None, "Should find Essen Hauptbahnhof"
        assert isinstance(station_id, str), "Station ID should be a string"
        print(f"\n✅ Found Essen Hauptbahnhof: {station_id}")
    
    @pytest.mark.asyncio
    async def test_find_station_dusseldorf_hbf(self, vrr_env):
        """Test finding Düsseldorf Hauptbahnhof"""
        station_id = await get_station_id("Düsseldorf Hauptbahnhof")
        
        assert station_id == 'de:05111:18235', "Should find Düsseldorf Hauptbahnhof"
        print(f"\n✅ Found Düsseldorf Hauptbahnhof: {station_id}")
    
    @pytest.mark.asyncio
    async def test_find_station_cologne_hbf(self, vrr_env):
        """Test finding Cologne Hauptbahnhof"""
        station_id = await get_station_id("Köln Hauptbahnhof")
        
        assert station_id is not None, "Should find Köln Hauptbahnhof"
        assert isinstance(station_id, str), "Station ID should be a string"
        print(f"\n✅ Found Köln Hauptbahnhof: {station_id}")


class TestDepartureFetching:
    """Test departure fetching functionality"""
    
    @pytest.mark.asyncio
    async def test_get_departures_by_station_name(self, vrr_env):
        """Test getting departures using station name"""
        departures = await get_departures(
            station_name="Essen Hauptbahnhof",
            limit=5
        )
        
        assert isinstance(departures, list), "Should return a list"
        print(f"\n✅ Found {len(departures)} departures from Essen Hauptbahnhof")
        
        if len(departures) > 0:
            dep = departures[0]
            assert isinstance(dep, PublicTransportDeparture)
            assert dep.line, "Departure should have a line"
            assert dep.destination, "Departure should have a destination"
            assert dep.planned_time, "Departure should have a planned time"
            print(f"   - Sample: {dep.line} to {dep.destination} at {dep.planned_time}")
    
    @pytest.mark.asyncio
    async def test_get_departures_by_station_id(self, vrr_env):
        """Test getting departures using station ID"""
        # First, get the station ID
        station_id = await get_station_id("Essen Hauptbahnhof")
        assert station_id is not None
        
        # Now fetch departures using the ID
        departures = await get_departures(
            station_id=station_id,
            limit=5
        )
        
        assert isinstance(departures, list), "Should return a list"
        print(f"\n✅ Found {len(departures)} departures using station ID")
    
    @pytest.mark.asyncio
    async def test_get_departures_with_different_limits(self, vrr_env):
        """Test fetching different numbers of departures"""
        for limit in [1, 5, 10]:
            departures = await get_departures(
                station_name="Essen Hauptbahnhof",
                limit=limit
            )
            
            assert len(departures) <= limit, f"Should not exceed limit of {limit}"
            print(f"\n✅ Limit {limit}: Got {len(departures)} departures")
    
    @pytest.mark.asyncio
    async def test_departures_have_valid_structure(self, vrr_env):
        """Test that returned departures have all required fields"""
        departures = await get_departures(
            station_name="Essen Hauptbahnhof",
            limit=3
        )
        
        if departures:
            for dep in departures:
                assert hasattr(dep, 'line'), "Should have line attribute"
                assert hasattr(dep, 'destination'), "Should have destination attribute"
                assert hasattr(dep, 'planned_time'), "Should have planned_time attribute"
                assert hasattr(dep, 'transport_type'), "Should have transport_type attribute"
                assert hasattr(dep, 'platform'), "Should have platform attribute"
                assert hasattr(dep, 'realtime'), "Should have realtime attribute"
                
                # Check types
                assert isinstance(dep.line, str), "Line should be string"
                assert isinstance(dep.destination, str), "Destination should be string"
                assert isinstance(dep.planned_time, str), "Planned time should be string"
                assert isinstance(dep.realtime, bool), "Realtime should be boolean"
            
            print(f"\n✅ All {len(departures)} departures have valid structure")


class TestJSONOutput:
    """Test JSON output functionality"""
    
    @pytest.mark.asyncio
    async def test_get_departures_json(self, vrr_env):
        """Test JSON output format"""
        result = await get_departures_json(
            station_name="Essen Hauptbahnhof",
            limit=5
        )
        
        assert isinstance(result, dict), "Should return a dictionary"
        assert "status" in result, "Should have status key"
        assert "departures" in result, "Should have departures key"
        assert "count" in result, "Should have count key"
        assert result["status"] in ["success", "no_departures"], "Should have valid status"
        assert isinstance(result["departures"], list), "Departures should be a list"
        assert result["count"] == len(result["departures"]), "Count should match departures length"
        
        print(f"\n✅ JSON output valid: {result['count']} departures")
        
        # Print sample departure JSON
        if result["departures"]:
            print(f"   Sample departure JSON: {result['departures'][0]}")


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_parse_departure_time(self):
        """Test time parsing"""
        # Test HHMM format
        assert _parse_departure_time("1530") == "15:30"
        assert _parse_departure_time("0845") == "08:45"
        assert _parse_departure_time("2359") == "23:59"
        
        # Test None and empty strings
        assert _parse_departure_time(None) is None
        assert _parse_departure_time("") is None
        
        print("\n✅ Time parsing works correctly")
    
    def test_calculate_delay(self):
        """Test delay calculation"""
        # On time
        assert _calculate_delay("15:30", "15:30") == 0
        
        # Delayed by 5 minutes
        assert _calculate_delay("15:30", "15:35") == 5
        
        # Early (should still be 0 or positive)
        result = _calculate_delay("15:30", "15:25")
        assert result is not None
        
        # None values
        assert _calculate_delay(None, "15:30") is None
        assert _calculate_delay("15:30", None) is None
        
        print("\n✅ Delay calculation works correctly")
    
    def test_departure_to_dict(self):
        """Test PublicTransportDeparture serialization"""
        dep = PublicTransportDeparture(
            line="U47",
            destination="Essen Rüttenscheid",
            planned_time="15:30",
            estimated_time="15:35",
            delay_minutes=5,
            transport_type="U-Bahn",
            platform="3",
            realtime=True
        )
        
        result = dep.to_dict()
        
        assert isinstance(result, dict), "to_dict should return dict"
        assert result["line"] == "U47"
        assert result["destination"] == "Essen Rüttenscheid"
        assert result["planned_time"] == "15:30"
        assert result["delay_minutes"] == 5
        assert result["realtime"] is True
        
        print("\n✅ Departure serialization works correctly")


class TestJourneyParsing:
    """Test parsing of full journeys"""

    async def _resolve_trip_ids(self):
        origin_id = await get_station_id("Dortmund Reinoldikirche")
        destination_id = await get_station_id("Dortmund Stadtkrone Ost")
        assert origin_id, "Origin station ID not found"
        assert destination_id, "Destination station ID not found"
        return origin_id, destination_id

    @pytest.mark.asyncio
    async def test_get_journeys_parses_steps(self, vrr_env):
        origin_id, destination_id = await self._resolve_trip_ids()

        journeys = await get_journeys(
            origin=origin_id,
            destination=destination_id,
            origin_type="stop",
            destination_type="stop",
            limit=1
        )

        if not journeys:
            pytest.skip("VRR returned no journeys for Dortmund Voßkuhle -> Stadtkrone Ost")

        journey = journeys[0]
        assert journey.length_minutes > 0
        assert journey.steps, "Journey should contain at least one step"
        first_step = journey.steps[0]
        assert first_step.mode, "Journey step should provide transport mode"
        assert first_step.duration_minutes > 0

    @pytest.mark.asyncio
    async def test_get_journeys_json_shape(self, vrr_env):
        origin_id, destination_id = await self._resolve_trip_ids()

        journeys = await get_journeys(
            origin=origin_id,
            destination=destination_id,
            origin_type="stop",
            destination_type="stop",
            limit=1
        )

        if len(journeys) == 0:
            pytest.skip("VRR returned no journeys")

        assert isinstance(journeys, list)
        first_journey = journeys[0]
        assert first_journey.length_minutes > 0
        assert first_journey.steps, "Journey should include steps"
        assert first_journey.steps[0].mode


class TestLineFiltering:
    """Test line filtering functionality"""
    
    @pytest.mark.asyncio
    async def test_get_serving_lines(self, vrr_env):
        """Test fetching serving lines for a station"""
        station_id = await get_station_id("Essen Hauptbahnhof")
        assert station_id is not None
        
        lines = await get_serving_lines(station_id)
        
        assert isinstance(lines, list), "Should return a list"
        assert len(lines) > 0, "Should find serving lines"
        
        # Check structure of returned lines - id and destination are always present
        for line in lines:
            assert "id" in line, "Line should have id"
            assert "destination" in line, "Line should have destination"
            # name, number, or disassembledName may vary depending on line type
        
        print(f"\n✅ Found {len(lines)} serving lines")
        if lines:
            # Use available name field (name, disassembledName, or product.name)
            line_names = []
            for line in lines[:5]:
                name = (line.get("disassembledName") or 
                       line.get("number") or 
                       line.get("name") or 
                       line.get("product", {}).get("name") or 
                       "Unknown")
                line_names.append(name)
            print(f"   Sample lines: {line_names}")
    
    @pytest.mark.asyncio
    async def test_find_line_id(self, vrr_env):
        """Test finding a specific line ID by line query"""
        station_id = await get_station_id("Essen Hauptbahnhof")
        assert station_id is not None
        
        # Get available lines first
        lines = await get_serving_lines(station_id)
        
        if lines:
            # Try to find the first line by its identifier
            first_line = lines[0]
            line_identifier = first_line.get("number") or first_line.get("disassembledName") or first_line.get("name") or "Unknown"
            
            line_id = await find_line_id(station_id, line_identifier)
            
            assert line_id is not None, f"Should find line {line_identifier}"
            assert isinstance(line_id, str), "Line ID should be a string"
            print(f"\n✅ Found line ID for {line_identifier}: {line_id}")
    
    @pytest.mark.asyncio
    async def test_find_nonexistent_line(self, vrr_env):
        """Test handling of nonexistent line"""
        station_id = await get_station_id("Essen Hauptbahnhof")
        assert station_id is not None
        
        line_id = await find_line_id(station_id, "XYZ999")
        
        assert line_id is None, "Should return None for nonexistent line"
        print("\n✅ Nonexistent line handled correctly")
    
    @pytest.mark.asyncio
    async def test_get_departures_filtered_by_line(self, vrr_env):
        """Test getting departures filtered by line query"""
        station_name = "Essen Hauptbahnhof"
        
        # First get all departures
        all_departures = await get_departures(
            station_name=station_name,
            limit=10
        )
        
        if all_departures:
            # Get the line number of the first departure
            filtered_line = all_departures[0].line
            
            # Now fetch departures for just that line
            filtered_departures = await get_departures(
                station_name=station_name,
                limit=10,
                line_query=filtered_line
            )
            
            assert isinstance(filtered_departures, list), "Should return a list"
            
            # All departures should be for the specified line
            if filtered_departures:
                for dep in filtered_departures:
                    assert dep.line == filtered_line, f"All departures should be for line {filtered_line}"
                
                print(f"\n✅ Got {len(filtered_departures)} departures for line {filtered_line}")
    
    @pytest.mark.asyncio
    async def test_get_departures_filtered_by_direction(self, vrr_env):
        """Test getting departures filtered by direction query"""
        station_name = "Essen Hauptbahnhof"
        
        # First get all departures
        all_departures = await get_departures(
            station_name=station_name,
            limit=20
        )
        
        if all_departures:
            # Get the destination of the first departure
            filtered_direction = all_departures[0].destination
            
            # Now fetch departures for just that direction
            filtered_departures = await get_departures(
                station_name=station_name,
                limit=20,
                direction_query=filtered_direction
            )
            
            assert isinstance(filtered_departures, list), "Should return a list"
            
            # All departures should be for the specified direction
            if filtered_departures:
                for dep in filtered_departures:
                    assert filtered_direction.lower() in dep.destination.lower(), f"All departures should go to {filtered_direction}"
                
                print(f"\n✅ Got {len(filtered_departures)} departures for direction {filtered_direction}")
    
    @pytest.mark.asyncio
    async def test_get_departures_filtered_by_line_and_direction(self, vrr_env):
        """Test getting departures filtered by both line and direction"""
        station_name = "Essen Hauptbahnhof"
        
        # First get all departures
        all_departures = await get_departures(
            station_name=station_name,
            limit=20
        )
        
        if all_departures:
            # Get line and direction from first departure
            filtered_line = all_departures[0].line
            filtered_direction = all_departures[0].destination
            
            # Now fetch departures with both filters
            filtered_departures = await get_departures(
                station_name=station_name,
                limit=20,
                line_query=filtered_line,
                direction_query=filtered_direction
            )
            
            assert isinstance(filtered_departures, list), "Should return a list"
            
            # All departures should match both criteria
            if filtered_departures:
                for dep in filtered_departures:
                    assert dep.line == filtered_line, f"Should match line {filtered_line}"
                    assert filtered_direction.lower() in dep.destination.lower(), f"Should go to {filtered_direction}"
                
                print(f"\n✅ Got {len(filtered_departures)} departures for line {filtered_line} to {filtered_direction}")
    
    @pytest.mark.asyncio
    async def test_get_departures_json_with_line_filter(self, vrr_env):
        """Test JSON output with line filtering"""
        station_name = "Essen Hauptbahnhof"
        
        # Get all departures first
        all_deps_result = await get_departures_json(
            station_name=station_name,
            limit=10
        )
        
        if all_deps_result["count"] > 0:
            # Get the line from first departure
            filtered_line = all_deps_result["departures"][0]["line"]
            
            # Fetch filtered departures as JSON
            result = await get_departures_json(
                station_name=station_name,
                limit=10,
                line_query=filtered_line
            )
            
            assert isinstance(result, dict), "Should return a dictionary"
            assert "status" in result, "Should have status key"
            assert "departures" in result, "Should have departures key"
            assert result["status"] in ["success", "no_departures"], "Should have valid status"
            
            # Check that all departures are for the requested line
            if result["count"] > 0:
                for dep_dict in result["departures"]:
                    assert dep_dict["line"] == filtered_line, f"All departures should be for line {filtered_line}"
            
            print(f"\n✅ JSON output with line filter valid: {result['count']} departures for line {filtered_line}")
    
    @pytest.mark.asyncio
    async def test_get_departures_json_with_direction_filter(self, vrr_env):
        """Test JSON output with direction filtering"""
        station_name = "Essen Hauptbahnhof"
        
        # Get all departures first
        all_deps_result = await get_departures_json(
            station_name=station_name,
            limit=20
        )
        
        if all_deps_result["count"] > 0:
            # Get the destination from first departure
            filtered_direction = all_deps_result["departures"][0]["destination"]
            
            # Fetch filtered departures as JSON
            result = await get_departures_json(
                station_name=station_name,
                limit=20,
                direction_query=filtered_direction
            )
            
            assert isinstance(result, dict), "Should return a dictionary"
            assert "status" in result, "Should have status key"
            assert "departures" in result, "Should have departures key"
            assert result["status"] in ["success", "no_departures"], "Should have valid status"
            
            # Check that all departures are for the requested direction
            if result["count"] > 0:
                for dep_dict in result["departures"]:
                    assert filtered_direction.lower() in dep_dict["destination"].lower(), f"All departures should go to {filtered_direction}"
            
            print(f"\n✅ JSON output with direction filter valid: {result['count']} departures for direction {filtered_direction}")


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_get_departures_with_missing_station(self, vrr_env):
        """Test handling of missing station"""
        departures = await get_departures(
            station_name="XYZ123NonExistent",
            limit=5
        )
        
        assert departures == [], "Should return empty list for missing station"
        print("\n✅ Missing station handled correctly")
    
    @pytest.mark.asyncio
    async def test_get_departures_with_missing_station_id(self, vrr_env):
        """Test handling of missing station ID"""
        departures = await get_departures(limit=5)
        
        assert departures == [], "Should return empty list when no station provided"
        print("\n✅ Missing station ID handled correctly")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "-s"])
