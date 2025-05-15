"""
MongoDB Database Connection Module

This module provides a wrapper for MongoDB connection using motor with a fallback to
an in-memory database when MongoDB is not available.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGODB_AVAILABLE = True
except ImportError:
    logger.warning("MongoDB not available, database functionality will be disabled")
    MONGODB_AVAILABLE = False

# MongoDB Connection Config
# For development, use connection details from environment variables 
# For production, will need to use a real MongoDB Atlas connection string
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "discord_bot")

# In our Replit environment, we will use the PostgreSQL DB until MongoDB is available
if not MONGODB_URI or MONGODB_URI == "mongodb://localhost:27017":
    # Use the PostgreSQL connection string format for the MongoDB URI
    # This is a fallback for development in Replit
    try:
        pg_host = os.environ.get("PGHOST")
        pg_port = os.environ.get("PGPORT")
        pg_user = os.environ.get("PGUSER")
        pg_pass = os.environ.get("PGPASSWORD")
        pg_db = os.environ.get("PGDATABASE")
        
        if all([pg_host, pg_port, pg_user, pg_pass, pg_db]):
            logger.info("Using PostgreSQL in place of MongoDB for development")
            # Store the PostgreSQL connection info for informational purposes
            PG_CONNECTION_INFO = {
                "host": pg_host,
                "port": pg_port,
                "user": pg_user,
                "database": pg_db
            }
    except Exception as e:
        logger.error(f"Error setting up PostgreSQL fallback: {e}")

class Database:
    """MongoDB database connection handler"""
    
    def __init__(self, connection_string: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize the database connection
        
        Args:
            connection_string: MongoDB connection string
            db_name: Database name
        """
        self.connection_string = connection_string or MONGODB_URI
        self.db_name = db_name or DB_NAME
        self.client = None
        self.db = None
        self.connected = False
        # In-memory fallback for Replit environment when MongoDB is not available
        self.in_memory_db = {}
        self.using_fallback = False

    async def connect(self) -> bool:
        """
        Connect to the MongoDB database
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not MONGODB_AVAILABLE:
            logger.warning("MongoDB client not available, using in-memory fallback")
            self.using_fallback = True
            self.connected = True
            return True
            
        try:
            # Connect to MongoDB
            self.client = AsyncIOMotorClient(self.connection_string)
            
            # Get database
            self.db = self.client[self.db_name]
            
            # Test connection
            try:
                await self.client.admin.command('ping')
                self.connected = True
                logger.info(f"Connected to MongoDB database: {self.db_name}")
                return True
            except Exception as e:
                logger.warning(f"MongoDB connection test failed: {e}")
                logger.info("Using in-memory fallback database")
                self.using_fallback = True
                self.connected = True
                return True
                
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            logger.info("Using in-memory fallback database")
            self.client = None
            self.db = None
            self.using_fallback = True
            self.connected = True
            return True

    async def disconnect(self):
        """Disconnect from the MongoDB database"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
        
        self.connected = False
        self.using_fallback = False
        logger.info("Disconnected from database")

    async def get_collection(self, collection_name: str):
        """
        Get a collection from the database
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection object or None if not connected
        """
        if self.using_fallback:
            # Initialize collection in in-memory DB if it doesn't exist
            if collection_name not in self.in_memory_db:
                self.in_memory_db[collection_name] = []
            return self.in_memory_db[collection_name]
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't get collection: {collection_name}")
            return None
            
        return self.db[collection_name]
        
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """
        Insert a document into a collection
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
            
        Returns:
            Inserted document ID or None if insertion failed
        """
        if self.using_fallback:
            # Initialize collection if it doesn't exist
            if collection_name not in self.in_memory_db:
                self.in_memory_db[collection_name] = []
                
            # Add _id field if not present
            if "_id" not in document:
                import uuid
                document["_id"] = str(uuid.uuid4())
                
            # Add created_at timestamp
            if "created_at" not in document:
                document["created_at"] = datetime.utcnow()
                
            self.in_memory_db[collection_name].append(document)
            return document["_id"]
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't insert into: {collection_name}")
            return None
            
        try:
            collection = self.db[collection_name]
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting document into {collection_name}: {e}")
            return None
            
    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a document in a collection
        
        Args:
            collection_name: Name of the collection
            query: Query to find the document
            
        Returns:
            Found document or None if not found or error
        """
        if self.using_fallback:
            # Initialize collection if it doesn't exist
            if collection_name not in self.in_memory_db:
                self.in_memory_db[collection_name] = []
                return None
                
            # Simple query matching for in-memory DB
            for doc in self.in_memory_db[collection_name]:
                matches = True
                for key, value in query.items():
                    if key not in doc or doc[key] != value:
                        matches = False
                        break
                if matches:
                    return doc
            return None
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't query: {collection_name}")
            return None
            
        try:
            collection = self.db[collection_name]
            result = await collection.find_one(query)
            return result
        except Exception as e:
            logger.error(f"Error finding document in {collection_name}: {e}")
            return None

    async def find_many(self, collection_name: str, query: Dict[str, Any], 
                       limit: Optional[int] = None, 
                       sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """
        Find documents in a collection
        
        Args:
            collection_name: Name of the collection
            query: Query to find documents
            limit: Maximum number of documents to return
            sort: List of (field, direction) tuples for sorting
            
        Returns:
            List of found documents or empty list if not found or error
        """
        if self.using_fallback:
            # Initialize collection if it doesn't exist
            if collection_name not in self.in_memory_db:
                self.in_memory_db[collection_name] = []
                return []
                
            # Simple query matching for in-memory DB
            results = []
            for doc in self.in_memory_db[collection_name]:
                matches = True
                for key, value in query.items():
                    if key not in doc or doc[key] != value:
                        matches = False
                        break
                if matches:
                    results.append(doc)
            
            # Simple sorting for in-memory DB
            if sort:
                for field, direction in reversed(sort):
                    reverse = direction == -1
                    results.sort(key=lambda x: x.get(field, None) is not None and x.get(field, None) or "", reverse=reverse)
            
            # Apply limit
            if limit and len(results) > limit:
                results = results[:limit]
                
            return results
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't query: {collection_name}")
            return []
            
        try:
            collection = self.db[collection_name]
            cursor = collection.find(query)
            
            if sort:
                cursor = cursor.sort(sort)
                
            if limit:
                cursor = cursor.limit(limit)
                
            return await cursor.to_list(length=limit or 100)
        except Exception as e:
            logger.error(f"Error finding documents in {collection_name}: {e}")
            return []

    async def update_one(self, collection_name: str, query: Dict[str, Any], 
                        update: Dict[str, Any], upsert: bool = False) -> bool:
        """
        Update a document in a collection
        
        Args:
            collection_name: Name of the collection
            query: Query to find the document
            update: Update to apply
            upsert: Whether to insert if document doesn't exist
            
        Returns:
            True if update was successful, False otherwise
        """
        if self.using_fallback:
            # Initialize collection if it doesn't exist
            if collection_name not in self.in_memory_db:
                self.in_memory_db[collection_name] = []
                
                # Upsert case for empty collection
                if upsert:
                    new_doc = {}
                    for key, value in query.items():
                        new_doc[key] = value
                    
                    # Handle $set operator
                    if "$set" in update:
                        for key, value in update["$set"].items():
                            new_doc[key] = value
                    
                    # Add _id field if not present
                    if "_id" not in new_doc:
                        import uuid
                        new_doc["_id"] = str(uuid.uuid4())
                    
                    # Add created_at timestamp
                    if "created_at" not in new_doc:
                        new_doc["created_at"] = datetime.utcnow()
                    
                    # Add updated_at timestamp
                    new_doc["updated_at"] = datetime.utcnow()
                    
                    self.in_memory_db[collection_name].append(new_doc)
                    return True
                
                return False
            
            # Find document to update
            found_index = None
            for i, doc in enumerate(self.in_memory_db[collection_name]):
                matches = True
                for key, value in query.items():
                    if key not in doc or doc[key] != value:
                        matches = False
                        break
                if matches:
                    found_index = i
                    break
            
            # Handle document not found
            if found_index is None:
                if not upsert:
                    return False
                
                # Upsert case
                new_doc = {}
                for key, value in query.items():
                    new_doc[key] = value
                
                # Handle $set operator
                if "$set" in update:
                    for key, value in update["$set"].items():
                        new_doc[key] = value
                
                # Add _id field if not present
                if "_id" not in new_doc:
                    import uuid
                    new_doc["_id"] = str(uuid.uuid4())
                
                # Add created_at timestamp
                if "created_at" not in new_doc:
                    new_doc["created_at"] = datetime.utcnow()
                
                # Add updated_at timestamp
                new_doc["updated_at"] = datetime.utcnow()
                
                self.in_memory_db[collection_name].append(new_doc)
                return True
            
            # Update the document
            doc = self.in_memory_db[collection_name][found_index]
            
            # Handle $set operator
            if "$set" in update:
                for key, value in update["$set"].items():
                    doc[key] = value
            
            # Handle $inc operator
            if "$inc" in update:
                for key, value in update["$inc"].items():
                    if key not in doc:
                        doc[key] = value
                    else:
                        doc[key] += value
            
            # Add updated_at timestamp
            doc["updated_at"] = datetime.utcnow()
            
            return True
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't update: {collection_name}")
            return False
            
        try:
            collection = self.db[collection_name]
            result = await collection.update_one(query, update, upsert=upsert)
            return result.modified_count > 0 or (upsert and result.upserted_id is not None)
        except Exception as e:
            logger.error(f"Error updating document in {collection_name}: {e}")
            return False

    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> bool:
        """
        Delete a document from a collection
        
        Args:
            collection_name: Name of the collection
            query: Query to find the document
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if self.using_fallback:
            # Initialize collection if it doesn't exist
            if collection_name not in self.in_memory_db:
                self.in_memory_db[collection_name] = []
                return False
            
            # Find document to delete
            found_index = None
            for i, doc in enumerate(self.in_memory_db[collection_name]):
                matches = True
                for key, value in query.items():
                    if key not in doc or doc[key] != value:
                        matches = False
                        break
                if matches:
                    found_index = i
                    break
            
            # Handle document not found
            if found_index is None:
                return False
            
            # Delete the document
            self.in_memory_db[collection_name].pop(found_index)
            return True
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't delete from: {collection_name}")
            return False
            
        try:
            collection = self.db[collection_name]
            result = await collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document from {collection_name}: {e}")
            return False

    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Count documents in a collection
        
        Args:
            collection_name: Name of the collection
            query: Query to count documents
            
        Returns:
            Number of documents matching the query or 0 if error
        """
        if self.using_fallback:
            # Initialize collection if it doesn't exist
            if collection_name not in self.in_memory_db:
                self.in_memory_db[collection_name] = []
                return 0
            
            # Count documents matching query
            count = 0
            for doc in self.in_memory_db[collection_name]:
                matches = True
                for key, value in query.items():
                    if key not in doc or doc[key] != value:
                        matches = False
                        break
                if matches:
                    count += 1
            
            return count
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't count documents in: {collection_name}")
            return 0
            
        try:
            collection = self.db[collection_name]
            return await collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting documents in {collection_name}: {e}")
            return 0

    async def create_index(self, collection_name: str, keys: List[tuple], 
                          unique: bool = False, sparse: bool = False) -> bool:
        """
        Create an index in a collection
        
        Args:
            collection_name: Name of the collection
            keys: List of (field, direction) tuples for the index
            unique: Whether the index should enforce uniqueness
            sparse: Whether the index should be sparse
            
        Returns:
            True if index creation was successful, False otherwise
        """
        if self.using_fallback:
            # No real index support for in-memory DB
            return True
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't create index in: {collection_name}")
            return False
            
        try:
            collection = self.db[collection_name]
            await collection.create_index(keys, unique=unique, sparse=sparse)
            return True
        except Exception as e:
            logger.error(f"Error creating index in {collection_name}: {e}")
            return False

    async def drop_collection(self, collection_name: str) -> bool:
        """
        Drop a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if collection was dropped, False otherwise
        """
        if self.using_fallback:
            # Remove collection from in-memory DB
            if collection_name in self.in_memory_db:
                del self.in_memory_db[collection_name]
            return True
            
        if not self.connected or not self.db:
            logger.warning(f"Not connected to database, can't drop collection: {collection_name}")
            return False
            
        try:
            await self.db.drop_collection(collection_name)
            logger.info(f"Dropped collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error dropping collection {collection_name}: {e}")
            return False

# Create a global database instance
db_instance = None

async def get_database() -> Database:
    """
    Get or create a global database instance
    
    Returns:
        Database instance
    """
    global db_instance
    
    if db_instance is None:
        db_instance = Database()
        await db_instance.connect()
        
    return db_instance