from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CommandMetadata:
    name: str
    module_path: str
    entrypoint: str
    description: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    loaded: bool = False


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: Dict[str, CommandMetadata] = {}
        self._aliases: Dict[str, str] = {}
        self._failed: Dict[str, str] = {}

    def register(self, metadata: CommandMetadata) -> None:
        if metadata.name in self._commands:
            raise ValueError(f"Command '{metadata.name}' is already registered.")

        # Prevent alias collisions with existing command names
        for alias in metadata.aliases:
            if alias in self._commands:
                raise ValueError(
                    f"Alias '{alias}' conflicts with an existing command name."
                )

        # Prevent alias collisions with existing aliases
        for alias in metadata.aliases:
            if alias in self._aliases:
                raise ValueError(
                    f"Alias '{alias}' is already mapped to command '{self._aliases[alias]}'."
                )

        self._commands[metadata.name] = metadata

        for alias in metadata.aliases:
            self._aliases[alias] = metadata.name

    def get(self, name: str) -> Optional[CommandMetadata]:
        # Direct command lookup
        if name in self._commands:
            return self._commands[name]

        # Alias lookup
        if name in self._aliases:
            command_name = self._aliases[name]
            return self._commands.get(command_name)

        return None

    def all_commands(self) -> List[str]:
        return list(self._commands.keys())

    def mark_failed(self, name: str, error: Exception) -> None:
        self._failed[name] = str(error)


# Global singleton instance
registry = CommandRegistry()
