import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from agents import function_tool

from .file_scanner import FileInfo
from .cache_manager import get_cache_manager


class TaskStatus(Enum):
    """Status of a task or file"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class BatchStrategy(Enum):
    """Different batching strategies"""
    BY_SIZE = "by_size"
    BY_LANGUAGE = "by_language"
    BY_DIRECTORY = "by_directory"
    MIXED = "mixed"


@dataclass
class ProcessingTask:
    """A single processing task"""
    task_id: str
    task_type: str  # "file_analysis", "dependency_extraction", etc.
    file_path: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    error_message: Optional[str] = None
    result: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class FileBatch:
    """A batch of files to process together"""
    batch_id: str
    files: List[str]
    estimated_tokens: int
    batch_type: str  # "small", "medium", "large"
    language_group: Optional[str] = None
    directory_group: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    tasks: List[ProcessingTask] = field(default_factory=list)


@dataclass
class ProcessingChecklistItem:
    """A checklist item (can be file or task level)"""
    item_id: str
    item_type: str  # "file", "task", "batch"
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependency_items: List[str] = field(default_factory=list)  # Must be completed first
    retry_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingSession:
    """A complete processing session with checklist"""
    session_id: str
    repo_path: str
    analysis_goal: str
    strategy: BatchStrategy
    checklist: List[ProcessingChecklistItem] = field(default_factory=list)
    batches: List[FileBatch] = field(default_factory=list)
    global_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    progress_file: Optional[str] = None


class BatchProcessor:
    """Manages batch processing with intelligent strategies"""
    
    def __init__(self, session: ProcessingSession):
        self.session = session
        self.cache_manager = get_cache_manager()
        self.max_retries = 3
        self.max_tokens_per_batch = 15000  # Conservative token limit
    
    def create_batches(self, files: List[FileInfo], strategy: BatchStrategy = BatchStrategy.MIXED) -> List[FileBatch]:
        """Create intelligent batches based on strategy"""
        batches = []
        
        if strategy == BatchStrategy.BY_SIZE:
            batches = self._create_size_based_batches(files)
        elif strategy == BatchStrategy.BY_LANGUAGE:
            batches = self._create_language_based_batches(files)
        elif strategy == BatchStrategy.BY_DIRECTORY:
            batches = self._create_directory_based_batches(files)
        else:  # MIXED strategy
            batches = self._create_mixed_batches(files)
        
        # Add batches to session
        self.session.batches = batches
        
        return batches
    
    def _create_size_based_batches(self, files: List[FileInfo]) -> List[FileBatch]:
        """Create batches based on file size and token estimates"""
        batches = []
        current_batch_files = []
        current_tokens = 0
        batch_counter = 0
        
        # Sort files by size (process large files first in separate batches)
        sorted_files = sorted(files, key=lambda f: f.estimated_tokens, reverse=True)
        
        for file_info in sorted_files:
            # Very large files get their own batch
            if file_info.estimated_tokens > self.max_tokens_per_batch * 0.8:
                if current_batch_files:
                    batches.append(self._create_batch(f"size_batch_{batch_counter}", current_batch_files, current_tokens, "large"))
                    batch_counter += 1
                    current_batch_files = []
                    current_tokens = 0
                
                batches.append(self._create_batch(f"size_batch_{batch_counter}", [file_info.path], file_info.estimated_tokens, "large"))
                batch_counter += 1
                continue
            
            # Check if adding this file would exceed token limit
            if current_tokens + file_info.estimated_tokens > self.max_tokens_per_batch:
                if current_batch_files:
                    batch_type = "large" if current_tokens > 10000 else "medium" if current_tokens > 5000 else "small"
                    batches.append(self._create_batch(f"size_batch_{batch_counter}", current_batch_files, current_tokens, batch_type))
                    batch_counter += 1
                    current_batch_files = []
                    current_tokens = 0
            
            current_batch_files.append(file_info.path)
            current_tokens += file_info.estimated_tokens
        
        # Add remaining files
        if current_batch_files:
            batch_type = "large" if current_tokens > 10000 else "medium" if current_tokens > 5000 else "small"
            batches.append(self._create_batch(f"size_batch_{batch_counter}", current_batch_files, current_tokens, batch_type))
        
        return batches
    
    def _create_language_based_batches(self, files: List[FileInfo]) -> List[FileBatch]:
        """Create batches grouped by programming language"""
        language_groups = {}
        
        # Group files by language
        for file_info in files:
            language = file_info.language
            if language not in language_groups:
                language_groups[language] = []
            language_groups[language].append(file_info)
        
        batches = []
        for language, lang_files in language_groups.items():
            # Further split by size within each language
            size_batches = self._create_size_based_batches(lang_files)
            for i, batch in enumerate(size_batches):
                batch.batch_id = f"lang_{language.lower()}_{i}"
                batch.language_group = language
                batches.append(batch)
        
        return batches
    
    def _create_directory_based_batches(self, files: List[FileInfo]) -> List[FileBatch]:
        """Create batches grouped by directory structure"""
        directory_groups = {}
        
        # Group files by their parent directory
        for file_info in files:
            directory = os.path.dirname(file_info.relative_path)
            if not directory:
                directory = "root"
            
            if directory not in directory_groups:
                directory_groups[directory] = []
            directory_groups[directory].append(file_info)
        
        batches = []
        for directory, dir_files in directory_groups.items():
            # Further split by size within each directory
            size_batches = self._create_size_based_batches(dir_files)
            for i, batch in enumerate(size_batches):
                batch.batch_id = f"dir_{directory.replace('/', '_').replace('\\', '_')}_{i}"
                batch.directory_group = directory
                batches.append(batch)
        
        return batches
    
    def _create_mixed_batches(self, files: List[FileInfo]) -> List[FileBatch]:
        """Create batches using mixed strategy (language + size + directory)"""
        # First group by language, then by directory within language, then by size
        language_groups = {}
        
        for file_info in files:
            language = file_info.language
            if language not in language_groups:
                language_groups[language] = {}
            
            directory = os.path.dirname(file_info.relative_path) or "root"
            if directory not in language_groups[language]:
                language_groups[language][directory] = []
            
            language_groups[language][directory].append(file_info)
        
        batches = []
        batch_counter = 0
        
        for language, dir_groups in language_groups.items():
            for directory, dir_files in dir_groups.items():
                # Create size-based batches within each language-directory group
                size_batches = self._create_size_based_batches(dir_files)
                for batch in size_batches:
                    batch.batch_id = f"mixed_{language.lower()}_{directory.replace('/', '_').replace('\\', '_')}_{batch_counter}"
                    batch.language_group = language
                    batch.directory_group = directory
                    batches.append(batch)
                    batch_counter += 1
        
        return batches
    
    def _create_batch(self, batch_id: str, file_paths: List[str], estimated_tokens: int, batch_type: str) -> FileBatch:
        """Create a FileBatch object"""
        return FileBatch(
            batch_id=batch_id,
            files=file_paths,
            estimated_tokens=estimated_tokens,
            batch_type=batch_type
        )
    
    def create_checklist(self, analysis_goals: List[str]) -> List[ProcessingChecklistItem]:
        """Create a mixed-mode checklist (file + task level)"""
        checklist = []
        item_counter = 0
        
        # 1. File-level checklist items
        for batch in self.session.batches:
            for file_path in batch.files:
                file_item = ProcessingChecklistItem(
                    item_id=f"file_{item_counter:04d}",
                    item_type="file",
                    description=f"Process file: {os.path.basename(file_path)}",
                    metadata={
                        "file_path": file_path,
                        "batch_id": batch.batch_id,
                        "language": batch.language_group,
                        "directory": batch.directory_group
                    }
                )
                checklist.append(file_item)
                item_counter += 1
        
        # 2. Task-level checklist items
        for goal in analysis_goals:
            task_item = ProcessingChecklistItem(
                item_id=f"task_{item_counter:04d}",
                item_type="task",
                description=f"Analysis goal: {goal}",
                dependency_items=[item.item_id for item in checklist if item.item_type == "file"],  # Depends on all files
                metadata={"analysis_type": goal}
            )
            checklist.append(task_item)
            item_counter += 1
        
        # 3. Batch-level checklist items
        for batch in self.session.batches:
            batch_item = ProcessingChecklistItem(
                item_id=f"batch_{item_counter:04d}",
                item_type="batch",
                description=f"Complete batch: {batch.batch_id}",
                dependency_items=[
                    item.item_id for item in checklist 
                    if item.item_type == "file" and item.metadata.get("batch_id") == batch.batch_id
                ],
                metadata={"batch_id": batch.batch_id}
            )
            checklist.append(batch_item)
            item_counter += 1
        
        self.session.checklist = checklist
        return checklist
    
    def get_next_ready_tasks(self, limit: int = 5) -> List[ProcessingChecklistItem]:
        """Get next tasks that are ready to be processed (dependencies satisfied)"""
        ready_tasks = []
        
        for item in self.session.checklist:
            if item.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            dependencies_met = True
            for dep_id in item.dependency_items:
                dep_item = next((i for i in self.session.checklist if i.item_id == dep_id), None)
                if dep_item and dep_item.status != TaskStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                ready_tasks.append(item)
                if len(ready_tasks) >= limit:
                    break
        
        return ready_tasks
    
    def update_task_status(self, task_id: str, status: TaskStatus, error_message: Optional[str] = None) -> bool:
        """Update the status of a checklist item"""
        for item in self.session.checklist:
            if item.item_id == task_id:
                item.status = status
                if error_message:
                    item.error_message = error_message
                if status == TaskStatus.FAILED:
                    item.retry_count += 1
                return True
        return False
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary"""
        total_items = len(self.session.checklist)
        status_counts = {}
        
        for status in TaskStatus:
            status_counts[status.value] = sum(1 for item in self.session.checklist if item.status == status)
        
        # Calculate progress by type
        type_progress = {}
        for item_type in ["file", "task", "batch"]:
            type_items = [item for item in self.session.checklist if item.item_type == item_type]
            type_total = len(type_items)
            type_completed = sum(1 for item in type_items if item.status == TaskStatus.COMPLETED)
            type_progress[item_type] = {
                "total": type_total,
                "completed": type_completed,
                "percentage": (type_completed / type_total * 100) if type_total > 0 else 0
            }
        
        return {
            "total_items": total_items,
            "status_counts": status_counts,
            "overall_progress": (status_counts.get("completed", 0) / total_items * 100) if total_items > 0 else 0,
            "type_progress": type_progress,
            "session_status": self.session.status.value,
            "failed_items": [
                {
                    "id": item.item_id,
                    "description": item.description,
                    "error": item.error_message,
                    "retry_count": item.retry_count
                }
                for item in self.session.checklist 
                if item.status == TaskStatus.FAILED
            ]
        }
    
    def save_progress(self, file_path: Optional[str] = None) -> str:
        """Save current session progress to file"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"./cache/session_{self.session.session_id}_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Convert session to serializable format
        session_data = {
            "session_id": self.session.session_id,
            "repo_path": self.session.repo_path,
            "analysis_goal": self.session.analysis_goal,
            "strategy": self.session.strategy.value,
            "created_at": self.session.created_at.isoformat(),
            "status": self.session.status.value,
            "checklist": [
                {
                    "item_id": item.item_id,
                    "item_type": item.item_type,
                    "description": item.description,
                    "status": item.status.value,
                    "dependency_items": item.dependency_items,
                    "retry_count": item.retry_count,
                    "error_message": item.error_message,
                    "metadata": item.metadata
                }
                for item in self.session.checklist
            ],
            "batches": [
                {
                    "batch_id": batch.batch_id,
                    "files": batch.files,
                    "estimated_tokens": batch.estimated_tokens,
                    "batch_type": batch.batch_type,
                    "language_group": batch.language_group,
                    "directory_group": batch.directory_group,
                    "status": batch.status.value
                }
                for batch in self.session.batches
            ],
            "global_context": self.session.global_context
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        self.session.progress_file = file_path
        return file_path
    
    @classmethod
    def load_progress(cls, file_path: str) -> 'BatchProcessor':
        """Load session progress from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct session
        session = ProcessingSession(
            session_id=data["session_id"],
            repo_path=data["repo_path"],
            analysis_goal=data["analysis_goal"],
            strategy=BatchStrategy(data["strategy"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            status=TaskStatus(data["status"]),
            progress_file=file_path
        )
        
        # Reconstruct checklist
        session.checklist = [
            ProcessingChecklistItem(
                item_id=item_data["item_id"],
                item_type=item_data["item_type"],
                description=item_data["description"],
                status=TaskStatus(item_data["status"]),
                dependency_items=item_data["dependency_items"],
                retry_count=item_data["retry_count"],
                error_message=item_data["error_message"],
                metadata=item_data["metadata"]
            )
            for item_data in data["checklist"]
        ]
        
        # Reconstruct batches
        session.batches = [
            FileBatch(
                batch_id=batch_data["batch_id"],
                files=batch_data["files"],
                estimated_tokens=batch_data["estimated_tokens"],
                batch_type=batch_data["batch_type"],
                language_group=batch_data["language_group"],
                directory_group=batch_data["directory_group"],
                status=TaskStatus(batch_data["status"])
            )
            for batch_data in data["batches"]
        ]
        
        session.global_context = data["global_context"]
        
        return cls(session)


# Function tools for external access
@function_tool
async def create_processing_session(
    repo_path: str,
    analysis_goal: str,
    strategy: str = "mixed"
) -> str:
    """
    Create a new batch processing session for comprehensive codebase analysis.
    
    Args:
        repo_path: Path to the repository to analyze
        analysis_goal: Description of what analysis to perform
        strategy: Batching strategy - "mixed", "by_size", "by_language", or "by_directory"
    
    Returns:
        Session details and initial setup information
    """
    try:
        import uuid
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        
        # Parse strategy
        try:
            batch_strategy = BatchStrategy(strategy.lower())
        except ValueError:
            batch_strategy = BatchStrategy.MIXED
        
        # Create session
        session = ProcessingSession(
            session_id=session_id,
            repo_path=repo_path,
            analysis_goal=analysis_goal,
            strategy=batch_strategy
        )
        
        # Create processor
        processor = BatchProcessor(session)
        
        # Get files using the internal scanner function
        from .file_scanner import _scan_repository
        files = _scan_repository(repo_path)
        
        # Create batches
        batches = processor.create_batches(files, batch_strategy)
        
        # Create checklist
        analysis_goals = [analysis_goal]
        checklist = processor.create_checklist(analysis_goals)
        
        # Save initial progress
        progress_file = processor.save_progress()
        
        # Format response
        output = f"""# 🚀 Processing Session Created

## 📋 Session Information
- **Session ID**: `{session_id}`
- **Repository**: `{repo_path}`
- **Analysis Goal**: {analysis_goal}
- **Strategy**: {strategy}
- **Progress File**: `{progress_file}`

## 🎯 Batching Results
- **Total Batches**: {len(batches)}
- **Strategy Used**: {batch_strategy.value}

### Batch Breakdown:
"""
        
        for batch in batches:
            output += f"- **{batch.batch_id}**: {len(batch.files)} files, {batch.estimated_tokens:,} tokens ({batch.batch_type})\n"
        
        output += f"""
## ✅ Checklist Summary
- **Total Items**: {len(checklist)}
- **File Tasks**: {len([i for i in checklist if i.item_type == 'file'])}
- **Analysis Tasks**: {len([i for i in checklist if i.item_type == 'task'])}
- **Batch Tasks**: {len([i for i in checklist if i.item_type == 'batch'])}

## 🔄 Next Steps
Use `get_processing_progress("{session_id}")` to check progress and `get_next_tasks("{session_id}")` to get ready tasks.
"""
        
        return output
        
    except Exception as e:
        return f"❌ Error creating processing session: {str(e)}"


@function_tool
async def get_processing_progress(session_id: str) -> str:
    """
    Get current progress of a processing session.
    
    Args:
        session_id: ID of the processing session
    
    Returns:
        Detailed progress report
    """
    try:
        # Find session file
        import glob
        session_files = glob.glob(f"./cache/session_{session_id}_*.json")
        if not session_files:
            return f"❌ Session not found: {session_id}"
        
        # Load the most recent session file
        session_file = sorted(session_files)[-1]
        processor = BatchProcessor.load_progress(session_file)
        
        # Get progress summary
        progress = processor.get_progress_summary()
        
        # Format output
        output = f"""# 📊 Processing Progress Report

## 🎯 Session: {session_id}
- **Repository**: `{processor.session.repo_path}`
- **Analysis Goal**: {processor.session.analysis_goal}
- **Status**: {progress['session_status']}
- **Overall Progress**: {progress['overall_progress']:.1f}%

## 📈 Progress by Type
"""
        
        for type_name, type_data in progress['type_progress'].items():
            output += f"- **{type_name.title()}**: {type_data['completed']}/{type_data['total']} completed ({type_data['percentage']:.1f}%)\n"
        
        if progress['failed_items']:
            output += "\n## ❌ Failed Items\n"
            for failed in progress['failed_items']:
                output += f"- `{failed['description']}`: {failed['error']} (retry {failed['retry_count']}/3)\n"
        
        # Get next ready tasks
        ready_tasks = processor.get_next_ready_tasks(3)
        if ready_tasks:
            output += "\n## 🔄 Next Ready Tasks\n"
            for i, task in enumerate(ready_tasks, 1):
                output += f"{i}. {task.description}\n"
        
        output += f"\nUse `get_next_tasks(\"{session_id}\")` to get detailed task information."
        
        return output
        
    except Exception as e:
        return f"❌ Error getting progress: {str(e)}"


@function_tool
async def get_next_tasks(session_id: str, limit: int = 5) -> str:
    """
    Get next ready tasks for a processing session.
    
    Args:
        session_id: ID of the processing session
        limit: Maximum number of tasks to return
    
    Returns:
        List of ready tasks with details
    """
    try:
        # Find session file
        import glob
        session_files = glob.glob(f"./cache/session_{session_id}_*.json")
        if not session_files:
            return f"❌ Session not found: {session_id}"
        
        # Load the most recent session file
        session_file = sorted(session_files)[-1]
        processor = BatchProcessor.load_progress(session_file)
        
        # Get next ready tasks
        ready_tasks = processor.get_next_ready_tasks(limit)
        
        if not ready_tasks:
            return f"""# 🔄 Next Ready Tasks (Session: {session_id})

## ✅ No tasks ready to process
All tasks are either completed, in progress, or waiting for dependencies.

Use `get_processing_progress("{session_id}")` to check current status.
"""
        
        output = f"""# 🔄 Next Ready Tasks (Session: {session_id})

## ✅ Ready to Process ({len(ready_tasks)} tasks):

"""
        
        for i, task in enumerate(ready_tasks, 1):
            output += f"### {i}. **{task.item_type.title()} Task**: `{task.item_id}`\n"
            output += f"- **Description**: {task.description}\n"
            output += f"- **Type**: {task.item_type}\n"
            
            if task.metadata:
                if 'file_path' in task.metadata:
                    output += f"- **File Path**: `{task.metadata['file_path']}`\n"
                if 'language' in task.metadata and task.metadata['language']:
                    output += f"- **Language**: {task.metadata['language']}\n"
                if 'batch_id' in task.metadata:
                    output += f"- **Batch**: {task.metadata['batch_id']}\n"
            
            if task.dependency_items:
                output += f"- **Dependencies**: {len(task.dependency_items)} items\n"
            else:
                output += f"- **Dependencies**: None\n"
            
            output += "\n"
        
        # Check for waiting tasks
        waiting_tasks = [item for item in processor.session.checklist 
                        if item.status == TaskStatus.PENDING and item not in ready_tasks]
        
        if waiting_tasks:
            output += "## 🔒 Waiting for Dependencies:\n"
            for task in waiting_tasks[:3]:  # Show first 3 waiting tasks
                output += f"- **{task.item_type.title()} Task**: {task.description} (waiting for {len(task.dependency_items)} dependencies)\n"
        
        output += f"\nUse `update_task_status(\"{session_id}\", task_id, status, error_msg)` to update task progress."
        
        return output
        
    except Exception as e:
        return f"❌ Error getting next tasks: {str(e)}"


@function_tool
async def update_task_status(
    session_id: str,
    task_id: str,
    status: str,
    error_message: Optional[str] = None
) -> str:
    """
    Update the status of a specific task in a processing session.
    
    Args:
        session_id: ID of the processing session
        task_id: ID of the task to update
        status: New status - "pending", "in_progress", "completed", "failed", "skipped"
        error_message: Error message if status is "failed"
    
    Returns:
        Update confirmation and next available tasks
    """
    try:
        # Parse status
        try:
            task_status = TaskStatus(status.lower())
        except ValueError:
            return f"❌ Invalid status: {status}. Use: pending, in_progress, completed, failed, skipped"
        
        # Find session file
        import glob
        session_files = glob.glob(f"./cache/session_{session_id}_*.json")
        if not session_files:
            return f"❌ Session not found: {session_id}"
        
        # Load the most recent session file
        session_file = sorted(session_files)[-1]
        processor = BatchProcessor.load_progress(session_file)
        
        # Update task status
        success = processor.update_task_status(task_id, task_status, error_message)
        if not success:
            return f"❌ Task not found: {task_id}"
        
        # Save updated progress
        processor.save_progress(session_file)
        
        # Get updated progress
        progress = processor.get_progress_summary()
        
        # Get newly available tasks
        ready_tasks = processor.get_next_ready_tasks(3)
        
        output = f"""# ✅ Task Status Updated

## 📝 Update Details
- **Session**: {session_id}
- **Task**: {task_id}
- **New Status**: {status}
- **Error Message**: {error_message or "None"}

## 📊 Updated Progress
- **Overall Progress**: {progress['overall_progress']:.1f}%
- **Ready Tasks**: {len(ready_tasks)} tasks now available

## 🔄 Next Recommendations
"""
        
        if task_status == TaskStatus.FAILED:
            output += f"- Task failed with error: {error_message}\n"
            # Find the actual task to get retry count
            failed_task = next((item for item in processor.session.checklist if item.item_id == task_id), None)
            if failed_task:
                output += f"- {3 - failed_task.retry_count} retries remaining\n"
        elif task_status == TaskStatus.COMPLETED:
            output += "- Task marked as completed successfully\n"
            if ready_tasks:
                output += f"- New tasks are now available for processing\n"
        
        if ready_tasks:
            output += "\n### 🔄 Newly Available Tasks:\n"
            for task in ready_tasks[:2]:  # Show first 2 newly available tasks
                output += f"- {task.description}\n"
        
        output += f"\nUse `get_next_tasks(\"{session_id}\")` to see all available tasks."
        
        return output
        
    except Exception as e:
        return f"❌ Error updating task status: {str(e)}"