"""
Databroker client for accessing scan metadata and results
Interfaces with Bluesky's Databroker for historical data retrieval
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from config.settings import settings

# Note: In production, these imports would be from actual packages
# from databroker import catalog
# from databroker.queries import TimeRange

logger = logging.getLogger(__name__)


class DatabrokerClient:
    """Client for interacting with Databroker catalog"""
    
    def __init__(self, catalog_name: Optional[str] = None):
        self.catalog_name = catalog_name or settings.DATABROKER_CATALOG
        self.catalog = None
        self._connected = False
        
    async def connect(self):
        """Initialize connection to Databroker catalog"""
        try:
            # In production, this would connect to actual Databroker
            # self.catalog = catalog[self.catalog_name]
            
            # For development, simulate connection
            self._connected = True
            logger.info(f"Connected to Databroker catalog: {self.catalog_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Databroker: {e}")
            self._connected = False
    
    async def disconnect(self):
        """Close connection to Databroker"""
        self._connected = False
        logger.info("Disconnected from Databroker")
    
    def is_connected(self) -> bool:
        """Check if connected to Databroker"""
        return self._connected
    
    async def get_last_scan(self) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for the most recent scan
        Returns scan information including ID, timestamp, plan, and summary
        """
        try:
            if not self._connected:
                await self.connect()
            
            # In production, this would query actual Databroker
            # run = self.catalog[-1]  # Get last run
            
            # For development, return simulated data
            scan_metadata = {
                "scan_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
                "uid": "a1b2c3d4",
                "timestamp": datetime.now() - timedelta(minutes=30),
                "plan_name": "scan",
                "plan_args": {
                    "detectors": ["pilatus"],
                    "motor": "motor_x",
                    "start": 0.0,
                    "stop": 5.0,
                    "num": 51
                },
                "exit_status": "success",
                "duration": 125.4,  # seconds
                "num_points": 51,
                "motors": ["motor_x"],
                "detectors": ["pilatus"],
                "metadata": {
                    "sample": "test_sample_001",
                    "user": "beamline_user",
                    "proposal": "2024-1-12345",
                    "energy": 12.4,  # keV
                    "temperature": 295.0  # K
                },
                "statistics": {
                    "max_counts": 15234,
                    "min_counts": 102,
                    "mean_counts": 5432,
                    "total_counts": 277032
                }
            }
            
            logger.info(f"Retrieved last scan: {scan_metadata['scan_id']}")
            return scan_metadata
            
        except Exception as e:
            logger.error(f"Error fetching last scan: {e}")
            return None
    
    async def get_scan_by_id(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a specific scan by ID
        """
        try:
            if not self._connected:
                await self.connect()
            
            # In production, query by UID
            # run = self.catalog[scan_id]
            
            # For development, return simulated data
            scan_metadata = {
                "scan_id": scan_id,
                "uid": scan_id[:8],
                "timestamp": datetime.now() - timedelta(hours=2),
                "plan_name": "count",
                "plan_args": {
                    "detectors": ["pilatus", "i0"],
                    "num": 10,
                    "delay": 1.0
                },
                "exit_status": "success",
                "duration": 10.5,
                "num_points": 10,
                "detectors": ["pilatus", "i0"],
                "metadata": {
                    "sample": "reference_001",
                    "user": "beamline_user",
                    "proposal": "2024-1-12345"
                }
            }
            
            logger.info(f"Retrieved scan: {scan_id}")
            return scan_metadata
            
        except Exception as e:
            logger.error(f"Error fetching scan {scan_id}: {e}")
            return None
    
    async def get_recent_scans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch metadata for recent scans
        """
        try:
            if not self._connected:
                await self.connect()
            
            # In production, query catalog with limit
            # runs = list(self.catalog.search(TimeRange(since="-1d"))[:limit])
            
            # For development, return simulated list
            scans = []
            base_time = datetime.now()
            
            for i in range(limit):
                scan = {
                    "scan_id": f"scan_{i:04d}",
                    "uid": f"uid_{i:04d}",
                    "timestamp": base_time - timedelta(minutes=30*i),
                    "plan_name": ["scan", "count", "list_scan"][i % 3],
                    "exit_status": "success" if i % 5 != 0 else "aborted",
                    "duration": 60 + i * 10,
                    "sample": f"sample_{i:03d}"
                }
                scans.append(scan)
            
            logger.info(f"Retrieved {len(scans)} recent scans")
            return scans
            
        except Exception as e:
            logger.error(f"Error fetching recent scans: {e}")
            return []
    
    async def get_scan_data(self, scan_id: str, stream: str = "primary") -> Optional[Dict[str, Any]]:
        """
        Fetch actual data from a scan (not just metadata)
        Returns arrays of data from detectors and motors
        """
        try:
            if not self._connected:
                await self.connect()
            
            # In production, fetch actual data arrays
            # run = self.catalog[scan_id]
            # dataset = run[stream].read()
            
            # For development, return simulated data
            import numpy as np
            
            x_data = np.linspace(0, 5, 51)
            y_data = 1000 * np.exp(-(x_data - 2.5)**2 / 0.5) + 100 * np.random.random(51)
            
            scan_data = {
                "scan_id": scan_id,
                "stream": stream,
                "data": {
                    "motor_x": x_data.tolist(),
                    "pilatus": y_data.tolist(),
                    "i0": (1000 + 50 * np.random.random(51)).tolist(),
                    "timestamp": [
                        (datetime.now() - timedelta(seconds=i)).isoformat() 
                        for i in range(51)
                    ]
                },
                "dims": {
                    "motor_x": ["time"],
                    "pilatus": ["time"],
                    "i0": ["time"]
                }
            }
            
            logger.info(f"Retrieved data for scan: {scan_id}")
            return scan_data
            
        except Exception as e:
            logger.error(f"Error fetching scan data: {e}")
            return None
    
    async def search_scans(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        plan_name: Optional[str] = None,
        sample: Optional[str] = None,
        user: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for scans based on various criteria
        """
        try:
            if not self._connected:
                await self.connect()
            
            # In production, build and execute query
            # query = {}
            # if start_time and end_time:
            #     query = TimeRange(since=start_time, until=end_time)
            # results = self.catalog.search(query)
            
            # For development, return filtered simulated data
            all_scans = await self.get_recent_scans(limit)
            
            # Apply filters
            filtered = all_scans
            if plan_name:
                filtered = [s for s in filtered if s.get("plan_name") == plan_name]
            if sample:
                filtered = [s for s in filtered if sample in s.get("sample", "")]
            
            logger.info(f"Search returned {len(filtered)} scans")
            return filtered[:limit]
            
        except Exception as e:
            logger.error(f"Error searching scans: {e}")
            return []
    
    async def get_scan_images(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve image data or file paths from a scan
        Used for displaying detector images in UI
        """
        try:
            if not self._connected:
                await self.connect()
            
            # In production, fetch actual image references
            # This might involve accessing external file systems or databases
            
            # For development, return simulated image metadata
            images = [
                {
                    "detector": "pilatus",
                    "index": 0,
                    "path": f"/data/images/{scan_id}/pilatus_000.tif",
                    "timestamp": datetime.now() - timedelta(minutes=5),
                    "exposure_time": 1.0,
                    "thumbnail": None  # Would contain base64 thumbnail in production
                },
                {
                    "detector": "pilatus",
                    "index": 25,
                    "path": f"/data/images/{scan_id}/pilatus_025.tif",
                    "timestamp": datetime.now() - timedelta(minutes=3),
                    "exposure_time": 1.0,
                    "thumbnail": None
                },
                {
                    "detector": "pilatus",
                    "index": 50,
                    "path": f"/data/images/{scan_id}/pilatus_050.tif",
                    "timestamp": datetime.now() - timedelta(minutes=1),
                    "exposure_time": 1.0,
                    "thumbnail": None
                }
            ]
            
            logger.info(f"Retrieved {len(images)} images for scan: {scan_id}")
            return images
            
        except Exception as e:
            logger.error(f"Error fetching scan images: {e}")
            return []
    
    async def export_scan(self, scan_id: str, format: str = "csv") -> Optional[str]:
        """
        Export scan data in various formats
        Returns file path or data string
        """
        try:
            if not self._connected:
                await self.connect()
            
            # Get scan data
            data = await self.get_scan_data(scan_id)
            if not data:
                return None
            
            # Export based on format
            if format == "csv":
                # In production, use pandas or similar
                csv_content = "motor_x,pilatus,i0\n"
                for i in range(len(data["data"]["motor_x"])):
                    csv_content += f"{data['data']['motor_x'][i]},{data['data']['pilatus'][i]},{data['data']['i0'][i]}\n"
                
                # Save to file
                export_path = f"/tmp/scan_{scan_id}.csv"
                # with open(export_path, 'w') as f:
                #     f.write(csv_content)
                
                logger.info(f"Exported scan {scan_id} to {export_path}")
                return export_path
                
            elif format == "json":
                import json
                export_path = f"/tmp/scan_{scan_id}.json"
                # with open(export_path, 'w') as f:
                #     json.dump(data, f, indent=2, default=str)
                return export_path
                
            else:
                logger.warning(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting scan: {e}")
            return None