"""
MongoDB Models

This module provides base model classes for MongoDB documents,
with validation and utility methods.
"""

import datetime
import logging
import copy
from typing import Dict, List, Any, Optional, Type, TypeVar, ClassVar, Generic, Union, get_type_hints, get_origin, get_args

# Import for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.safe_mongodb import SafeMongoDBClient, SafeMongoDBResult, SafeDocument

# Configure logger
logger = logging.getLogger("mongodb_models")

# Type variable for model class
T = TypeVar('T', bound='MongoModel')

class MongoModel:
    """
    Base class for MongoDB document models
    
    This class provides common functionality for MongoDB document models,
    including validation, serialization, and CRUD operations.
    
    Class Attributes:
        collection_name: Name of the MongoDB collection for the model
        indexes: List of index specifications for the collection
        
    Attributes:
        _id: MongoDB document ID
    """
    
    collection_name: ClassVar[str] = "unknown"
    indexes: ClassVar[List[Dict[str, Any]]] = []
    
    def __init__(self, **kwargs):
        """
        Initialize the model with the given attributes
        
        Args:
            **kwargs: Model attributes
        """
        self._id = kwargs.pop('_id', None)
        
        # Set attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary
        
        Returns:
            Dictionary representation of the model
        """
        result = {}
        
        # Add MongoDB ID if it exists
        if self._id is not None:
            result['_id'] = self._id
        
        # Add other attributes
        for key, value in self.__dict__.items():
            if not key.startswith('_') and key != 'collection_name' and key != 'indexes':
                result[key] = value
        
        return result
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model instance from a dictionary
        
        Args:
            data: Dictionary data
            
        Returns:
            Model instance
        """
        # Convert MongoDB date fields to datetime objects
        processed_data = copy.deepcopy(data)
        
        # Handle specific data types
        for key, value in data.items():
            if isinstance(value, dict) and '$date' in value:
                # MongoDB date
                processed_data[key] = datetime.datetime.fromtimestamp(value['$date'] / 1000.0)
        
        # Create the instance
        return cls(**processed_data)
    
    async def save(self, db_client: 'SafeMongoDBClient') -> 'SafeMongoDBResult':
        """
        Save the model to the database
        
        Args:
            db_client: MongoDB client
            
        Returns:
            Result of the save operation
        """
        data = self.to_dict()
        
        if self._id is not None:
            # Update existing document
            result = await db_client.update_one(
                self.collection_name,
                {"_id": self._id},
                {"$set": data}
            )
        else:
            # Insert new document
            result = await db_client.insert_one(
                self.collection_name,
                data
            )
            
            if result.success and result.data:
                self._id = result.data.inserted_id
        
        return result
    
    async def delete(self, db_client: 'SafeMongoDBClient') -> 'SafeMongoDBResult':
        """
        Delete the model from the database
        
        Args:
            db_client: MongoDB client
            
        Returns:
            Result of the delete operation
        """
        if self._id is None:
            from utils.safe_mongodb import SafeMongoDBResult
            return SafeMongoDBResult.error_result(
                "Cannot delete model without _id",
                error_type="ValidationError"
            )
        
        return await db_client.delete_one(
            self.collection_name,
            {"_id": self._id}
        )
    
    @classmethod
    async def get_by_id(cls: Type[T], db_client: 'SafeMongoDBClient', id: Any) -> Optional[T]:
        """
        Get a model by its ID
        
        Args:
            db_client: MongoDB client
            id: Document ID
            
        Returns:
            Model instance or None if not found
        """
        result = await db_client.find_one(
            cls.collection_name,
            {"_id": id}
        )
        
        if result.success and result.data:
            return cls.from_dict(result.data)
        
        return None
    
    @classmethod
    async def find(cls: Type[T], db_client: 'SafeMongoDBClient', query: Dict[str, Any], 
                  sort: Optional[List[tuple]] = None,
                  limit: Optional[int] = None,
                  skip: Optional[int] = None) -> List[T]:
        """
        Find models matching a query
        
        Args:
            db_client: MongoDB client
            query: Query filter
            sort: Sort specification
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            
        Returns:
            List of model instances
        """
        result = await db_client.find_many(
            cls.collection_name,
            query,
            sort=sort,
            limit=limit,
            skip=skip
        )
        
        if result.success and result.data:
            return [cls.from_dict(doc) for doc in result.data]
        
        return []
    
    @classmethod
    async def find_one(cls: Type[T], db_client: 'SafeMongoDBClient', query: Dict[str, Any]) -> Optional[T]:
        """
        Find a single model matching a query
        
        Args:
            db_client: MongoDB client
            query: Query filter
            
        Returns:
            Model instance or None if not found
        """
        result = await db_client.find_one(
            cls.collection_name,
            query
        )
        
        if result.success and result.data:
            return cls.from_dict(result.data)
        
        return None
    
    @classmethod
    async def count(cls, db_client: 'SafeMongoDBClient', query: Dict[str, Any]) -> int:
        """
        Count models matching a query
        
        Args:
            db_client: MongoDB client
            query: Query filter
            
        Returns:
            Count of matching documents
        """
        result = await db_client.count_documents(
            cls.collection_name,
            query
        )
        
        if result.success:
            return result.data
        
        return 0
    
    @classmethod
    async def ensure_indexes(cls, db_client: 'SafeMongoDBClient') -> bool:
        """
        Create the defined indexes on the collection
        
        Args:
            db_client: MongoDB client
            
        Returns:
            Whether the indexes were created successfully
        """
        if not cls.indexes:
            return True
        
        collection_result = await db_client.get_collection(cls.collection_name)
        if not collection_result.success:
            logger.error(f"Failed to get collection {cls.collection_name} for creating indexes")
            return False
        
        collection = collection_result.data
        
        try:
            for index_spec in cls.indexes:
                keys = index_spec.get("keys", {})
                options = index_spec.get("options", {})
                
                if keys:
                    await collection.create_index(list(keys.items()), **options)
            
            logger.info(f"Created indexes for {cls.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating indexes for {cls.collection_name}: {e}")
            return False
    
    @classmethod
    async def aggregate(cls: Type[T], db_client: 'SafeMongoDBClient', pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run an aggregation pipeline
        
        Args:
            db_client: MongoDB client
            pipeline: Aggregation pipeline
            
        Returns:
            List of result documents
        """
        result = await db_client.aggregate(
            cls.collection_name,
            pipeline
        )
        
        if result.success and result.data:
            return result.data
        
        return []

# Guild model for Discord servers
class Guild(MongoModel):
    """
    Model for Discord guild (server) data
    """
    collection_name = "guilds"
    indexes = [
        {"keys": {"guild_id": 1}, "options": {"unique": True}},
        {"keys": {"premium_tier": 1}, "options": {}}
    ]
    
    def __init__(
        self,
        guild_id: int,
        name: str = "",
        premium_tier: int = 0,
        premium_until: Optional[datetime.datetime] = None,
        prefix: str = "!",
        settings: Dict[str, Any] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
        **kwargs
    ):
        """
        Initialize a guild model
        
        Args:
            guild_id: Discord guild ID
            name: Guild name
            premium_tier: Premium tier (0-3)
            premium_until: When premium expires
            prefix: Command prefix
            settings: Guild settings
            created_at: When the guild was created
            updated_at: When the guild was last updated
            **kwargs: Additional attributes
        """
        super().__init__(**kwargs)
        self.guild_id = guild_id
        self.name = name
        self.premium_tier = premium_tier
        self.premium_until = premium_until
        self.prefix = prefix
        self.settings = settings or {}
        self.created_at = created_at or datetime.datetime.utcnow()
        self.updated_at = updated_at or datetime.datetime.utcnow()
    
    @classmethod
    async def get_by_guild_id(cls, db_client: 'SafeMongoDBClient', guild_id: int) -> Optional['Guild']:
        """
        Get a guild by its Discord ID
        
        Args:
            db_client: MongoDB client
            guild_id: Discord guild ID
            
        Returns:
            Guild instance or None if not found
        """
        return await cls.find_one(db_client, {"guild_id": guild_id})
    
    @classmethod
    async def get_or_create(cls, db_client: 'SafeMongoDBClient', guild_id: int, name: str = "") -> 'Guild':
        """
        Get a guild or create it if it doesn't exist
        
        Args:
            db_client: MongoDB client
            guild_id: Discord guild ID
            name: Guild name
            
        Returns:
            Guild instance
        """
        guild = await cls.get_by_guild_id(db_client, guild_id)
        if guild is None:
            guild = cls(guild_id=guild_id, name=name)
            await guild.save(db_client)
        return guild

# User model for Discord users
class User(MongoModel):
    """
    Model for Discord user data
    """
    collection_name = "users"
    indexes = [
        {"keys": {"user_id": 1}, "options": {"unique": True}}
    ]
    
    def __init__(
        self,
        user_id: int,
        name: str = "",
        settings: Dict[str, Any] = None,
        permissions: Dict[str, Any] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
        **kwargs
    ):
        """
        Initialize a user model
        
        Args:
            user_id: Discord user ID
            name: User name
            settings: User settings
            permissions: User permissions
            created_at: When the user was created
            updated_at: When the user was last updated
            **kwargs: Additional attributes
        """
        super().__init__(**kwargs)
        self.user_id = user_id
        self.name = name
        self.settings = settings or {}
        self.permissions = permissions or {}
        self.created_at = created_at or datetime.datetime.utcnow()
        self.updated_at = updated_at or datetime.datetime.utcnow()
    
    @classmethod
    async def get_by_user_id(cls, db_client: 'SafeMongoDBClient', user_id: int) -> Optional['User']:
        """
        Get a user by their Discord ID
        
        Args:
            db_client: MongoDB client
            user_id: Discord user ID
            
        Returns:
            User instance or None if not found
        """
        return await cls.find_one(db_client, {"user_id": user_id})
    
    @classmethod
    async def get_or_create(cls, db_client: 'SafeMongoDBClient', user_id: int, name: str = "") -> 'User':
        """
        Get a user or create them if they don't exist
        
        Args:
            db_client: MongoDB client
            user_id: Discord user ID
            name: User name
            
        Returns:
            User instance
        """
        user = await cls.get_by_user_id(db_client, user_id)
        if user is None:
            user = cls(user_id=user_id, name=name)
            await user.save(db_client)
        return user

# Helper function to create model instances with proper type checking
def create_model(model_class: Type[T], data: Dict[str, Any]) -> T:
    """
    Create a model instance with type checking
    
    Args:
        model_class: Model class
        data: Model data
        
    Returns:
        Model instance
    """
    # Get expected types from type hints
    type_hints = get_type_hints(model_class.__init__)
    
    # Process data to match expected types
    processed_data = {}
    for key, value in data.items():
        if key in type_hints:
            expected_type = type_hints[key]
            
            # Check if the expected type is a Union
            if get_origin(expected_type) is Union:
                # Just use the value as-is for Union types
                processed_data[key] = value
            elif expected_type is datetime.datetime and isinstance(value, str):
                # Convert string to datetime
                try:
                    processed_data[key] = datetime.datetime.fromisoformat(value)
                except ValueError:
                    # Try other format
                    try:
                        processed_data[key] = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Keep original value
                        processed_data[key] = value
            else:
                # Use value as-is
                processed_data[key] = value
        else:
            # No type hint, use value as-is
            processed_data[key] = value
    
    # Create the instance
    return model_class(**processed_data)