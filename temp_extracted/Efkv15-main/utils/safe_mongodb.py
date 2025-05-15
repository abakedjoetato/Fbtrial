"""
Safe MongoDB Module

This module provides a safe interface for MongoDB operations,
with proper error handling and type safety.
"""

import asyncio
import logging
import traceback
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, cast

# Set up logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')

class SafeMongoDBResult(Generic[T]):
    """
    A safe wrapper for MongoDB operation results.
    
    This class wraps the result of a MongoDB operation with proper
    error handling and result access.
    """
    
    def __init__(self, success: bool = False, data: Optional[T] = None, error: Optional[Exception] = None):
        """
        Initialize a SafeMongoDBResult.
        
        Args:
            success: Whether the operation was successful
            data: The data returned by the operation
            error: The exception that occurred during the operation
        """
        self.success = success
        self.data = data
        self.error = error
        self.error_message = str(error) if error else ""
    
    def __bool__(self) -> bool:
        """Return whether the operation was successful."""
        return self.success and self.data is not None
    
    @property
    def value(self) -> Optional[T]:
        """Get the data from the result."""
        return self.data
    
    @property
    def has_error(self) -> bool:
        """Return whether an error occurred."""
        return self.error is not None
    
    @classmethod
    def success_result(cls, data: T) -> 'SafeMongoDBResult[T]':
        """Create a successful result."""
        return cls(success=True, data=data)
    
    @classmethod
    def error_result(cls, error: Exception) -> 'SafeMongoDBResult[T]':
        """Create an error result."""
        return cls(success=False, error=error)

# Globals
_mongo_client = None
_mongo_db = None

async def setup_mongodb(connection_string: str, database_name: str) -> bool:
    """
    Set up MongoDB connection.
    
    Args:
        connection_string: MongoDB connection string
        database_name: MongoDB database name
        
    Returns:
        Whether the setup was successful
    """
    global _mongo_client, _mongo_db
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        _mongo_client = AsyncIOMotorClient(connection_string)
        _mongo_db = _mongo_client[database_name]
        
        # Test connection
        await _mongo_db.command("ping")
        logger.info(f"Connected to MongoDB database: {database_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        _mongo_client = None
        _mongo_db = None
        return False

def get_database():
    """Get the MongoDB database."""
    return _mongo_db

def get_collection(collection_name: str):
    """
    Get a MongoDB collection.
    
    Args:
        collection_name: Collection name
        
    Returns:
        MongoDB collection or None
    """
    if not _mongo_db:
        logger.warning("MongoDB not initialized")
        return None
    
    return _mongo_db[collection_name]

async def find_one(collection_name: str, filter: Dict[str, Any], **kwargs) -> SafeMongoDBResult:
    """
    Find a single document in a collection.
    
    Args:
        collection_name: Collection name
        filter: Filter to apply
        **kwargs: Additional arguments for find_one
        
    Returns:
        SafeMongoDBResult with the document
    """
    collection = get_collection(collection_name)
    if not collection:
        return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
    
    try:
        result = await collection.find_one(filter, **kwargs)
        return SafeMongoDBResult.success_result(result)
    except Exception as e:
        logger.error(f"Error in find_one: {e}")
        return SafeMongoDBResult.error_result(e)

async def find(collection_name: str, filter: Dict[str, Any], **kwargs) -> SafeMongoDBResult[List[Dict[str, Any]]]:
    """
    Find documents in a collection.
    
    Args:
        collection_name: Collection name
        filter: Filter to apply
        **kwargs: Additional arguments for find
        
    Returns:
        SafeMongoDBResult with the documents
    """
    collection = get_collection(collection_name)
    if not collection:
        return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
    
    try:
        cursor = collection.find(filter, **kwargs)
        result = await cursor.to_list(length=None)
        return SafeMongoDBResult.success_result(result)
    except Exception as e:
        logger.error(f"Error in find: {e}")
        return SafeMongoDBResult.error_result(e)

async def insert_one(collection_name: str, document: Dict[str, Any], **kwargs) -> SafeMongoDBResult:
    """
    Insert a document into a collection.
    
    Args:
        collection_name: Collection name
        document: Document to insert
        **kwargs: Additional arguments for insert_one
        
    Returns:
        SafeMongoDBResult with the insert result
    """
    collection = get_collection(collection_name)
    if not collection:
        return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
    
    try:
        result = await collection.insert_one(document, **kwargs)
        return SafeMongoDBResult.success_result(result)
    except Exception as e:
        logger.error(f"Error in insert_one: {e}")
        return SafeMongoDBResult.error_result(e)

async def update_one(collection_name: str, filter: Dict[str, Any], update: Dict[str, Any], **kwargs) -> SafeMongoDBResult:
    """
    Update a document in a collection.
    
    Args:
        collection_name: Collection name
        filter: Filter to apply
        update: Update to apply
        **kwargs: Additional arguments for update_one
        
    Returns:
        SafeMongoDBResult with the update result
    """
    collection = get_collection(collection_name)
    if not collection:
        return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
    
    try:
        result = await collection.update_one(filter, update, **kwargs)
        return SafeMongoDBResult.success_result(result)
    except Exception as e:
        logger.error(f"Error in update_one: {e}")
        return SafeMongoDBResult.error_result(e)

async def delete_one(collection_name: str, filter: Dict[str, Any], **kwargs) -> SafeMongoDBResult:
    """
    Delete a document from a collection.
    
    Args:
        collection_name: Collection name
        filter: Filter to apply
        **kwargs: Additional arguments for delete_one
        
    Returns:
        SafeMongoDBResult with the delete result
    """
    collection = get_collection(collection_name)
    if not collection:
        return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
    
    try:
        result = await collection.delete_one(filter, **kwargs)
        return SafeMongoDBResult.success_result(result)
    except Exception as e:
        logger.error(f"Error in delete_one: {e}")
        return SafeMongoDBResult.error_result(e)

async def count_documents(collection_name: str, filter: Dict[str, Any], **kwargs) -> SafeMongoDBResult[int]:
    """
    Count documents in a collection.
    
    Args:
        collection_name: Collection name
        filter: Filter to apply
        **kwargs: Additional arguments for count_documents
        
    Returns:
        SafeMongoDBResult with the count
    """
    collection = get_collection(collection_name)
    if not collection:
        return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
    
    try:
        result = await collection.count_documents(filter, **kwargs)
        return SafeMongoDBResult.success_result(result)
    except Exception as e:
        logger.error(f"Error in count_documents: {e}")
        return SafeMongoDBResult.error_result(e)

class SafeMongoDBClient:
    """
    A client for performing safe MongoDB operations.
    
    This client wraps common MongoDB operations with proper error handling.
    """
    
    def __init__(self, db=None):
        """
        Initialize a SafeMongoDBClient.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db or _mongo_db
    
    def get_collection(self, collection_name: str):
        """
        Get a MongoDB collection.
        
        Args:
            collection_name: Collection name
            
        Returns:
            MongoDB collection or None
        """
        if not self.db:
            logger.warning("MongoDB not initialized")
            return None
        
        return self.db[collection_name]
    
    async def find_one(self, collection_name: str, filter: Dict[str, Any], **kwargs) -> SafeMongoDBResult:
        """
        Find a single document in a collection.
        
        Args:
            collection_name: Collection name
            filter: Filter to apply
            **kwargs: Additional arguments for find_one
            
        Returns:
            SafeMongoDBResult with the document
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
        
        try:
            result = await collection.find_one(filter, **kwargs)
            return SafeMongoDBResult.success_result(result)
        except Exception as e:
            logger.error(f"Error in find_one: {e}")
            return SafeMongoDBResult.error_result(e)
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any], **kwargs) -> SafeMongoDBResult:
        """
        Insert a document into a collection.
        
        Args:
            collection_name: Collection name
            document: Document to insert
            **kwargs: Additional arguments for insert_one
            
        Returns:
            SafeMongoDBResult with the insert result
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
        
        try:
            result = await collection.insert_one(document, **kwargs)
            return SafeMongoDBResult.success_result(result)
        except Exception as e:
            logger.error(f"Error in insert_one: {e}")
            return SafeMongoDBResult.error_result(e)
            
    async def update_one(self, collection_name: str, filter: Dict[str, Any], update: Dict[str, Any], **kwargs) -> SafeMongoDBResult:
        """
        Update a document in a collection.
        
        Args:
            collection_name: Collection name
            filter: Filter to apply
            update: Update to apply
            **kwargs: Additional arguments for update_one
            
        Returns:
            SafeMongoDBResult with the update result
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
        
        try:
            result = await collection.update_one(filter, update, **kwargs)
            return SafeMongoDBResult.success_result(result)
        except Exception as e:
            logger.error(f"Error in update_one: {e}")
            return SafeMongoDBResult.error_result(e)
    
    async def delete_one(self, collection_name: str, filter: Dict[str, Any], **kwargs) -> SafeMongoDBResult:
        """
        Delete a document from a collection.
        
        Args:
            collection_name: Collection name
            filter: Filter to apply
            **kwargs: Additional arguments for delete_one
            
        Returns:
            SafeMongoDBResult with the delete result
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
        
        try:
            result = await collection.delete_one(filter, **kwargs)
            return SafeMongoDBResult.success_result(result)
        except Exception as e:
            logger.error(f"Error in delete_one: {e}")
            return SafeMongoDBResult.error_result(e)
            
    async def find_many(self, collection_name: str, filter: Dict[str, Any], **kwargs) -> SafeMongoDBResult[List[Dict[str, Any]]]:
        """
        Find documents in a collection.
        
        Args:
            collection_name: Collection name
            filter: Filter to apply
            **kwargs: Additional arguments for find
            
        Returns:
            SafeMongoDBResult with the documents
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
        
        try:
            cursor = collection.find(filter, **kwargs)
            result = await cursor.to_list(length=None)
            return SafeMongoDBResult.success_result(result)
        except Exception as e:
            logger.error(f"Error in find_many: {e}")
            return SafeMongoDBResult.error_result(e)
            
    async def count_documents(self, collection_name: str, filter: Dict[str, Any], **kwargs) -> SafeMongoDBResult[int]:
        """
        Count documents in a collection.
        
        Args:
            collection_name: Collection name
            filter: Filter to apply
            **kwargs: Additional arguments for count_documents
            
        Returns:
            SafeMongoDBResult with the count
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
        
        try:
            result = await collection.count_documents(filter, **kwargs)
            return SafeMongoDBResult.success_result(result)
        except Exception as e:
            logger.error(f"Error in count_documents: {e}")
            return SafeMongoDBResult.error_result(e)
            
    async def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]], **kwargs) -> SafeMongoDBResult[List[Dict[str, Any]]]:
        """
        Run an aggregation pipeline on a collection.
        
        Args:
            collection_name: Collection name
            pipeline: Aggregation pipeline
            **kwargs: Additional arguments for aggregate
            
        Returns:
            SafeMongoDBResult with the aggregation results
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return SafeMongoDBResult.error_result(Exception("MongoDB not initialized"))
        
        try:
            cursor = collection.aggregate(pipeline, **kwargs)
            result = await cursor.to_list(length=None)
            return SafeMongoDBResult.success_result(result)
        except Exception as e:
            logger.error(f"Error in aggregate: {e}")
            return SafeMongoDBResult.error_result(e)

class SafeDocument(Dict[str, Any]):
    """
    Safe wrapper for MongoDB documents with additional helper methods.
    
    This class provides a safer way to access document fields with
    proper error handling and default values.
    """
    
    def __init__(self, document: Optional[Dict[str, Any]] = None):
        """
        Initialize a SafeDocument.
        
        Args:
            document: The MongoDB document to wrap
        """
        super().__init__()
        if document:
            self.update(document)
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the document with a default.
        
        Args:
            key: The key to look up
            default: Default value if the key is not found
            
        Returns:
            The value at the key or the default
        """
        return super().get(key, default)