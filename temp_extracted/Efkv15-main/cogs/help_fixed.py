"""
Help Commands Cog (Fixed Version)

This module provides help commands for the bot using py-cord compatibility.
"""

import logging
import asyncio
import datetime
from typing import Dict, List, Optional, Union, Any, Set

from discord_compat_layer import (
    Embed, Color, commands, Interaction, app_commands, 
    slash_command, ui, View, Button, ButtonStyle, Member, SelectOption
)

logger = logging.getLogger(__name__)

class HelpCog(commands.Cog):
    """Help commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.command_categories = {
            "General": "Basic bot commands",
            "Admin": "Server administration commands",
            "Settings": "Bot configuration commands",
            "Stats": "Player and server statistics",
            "Premium": "Premium-only features",
            "Utility": "Utility commands",
            "Game": "Game-related commands"
        }
        logger.info("Help Fixed cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready"""
        logger.info("Help Fixed cog ready")
    
    @slash_command(name="bothelp", description="Show bot commands and how to use them")
    async def help_command(self, ctx: Interaction, command: Optional[str] = None):
        """Show help information about commands"""
        # Defer the response to avoid timeout
        await ctx.response.defer()
        
        if command:
            # Show help for a specific command
            await self._show_command_help(ctx, command)
        else:
            # Show general help with categories
            await self._show_general_help(ctx)
    
    async def _show_general_help(self, ctx: Interaction):
        """Show general help information with command categories"""
        embed = Embed(
            title="Bot Help",
            description="Select a category to view available commands",
            color=Color.blue()
        )
        
        # Add categories as fields
        for category, description in self.command_categories.items():
            embed.add_field(
                name=category,
                value=f"```/help {category.lower()}```\n{description}",
                inline=True
            )
        
        # Create dropdown for categories
        view = self.HelpView(self.bot, ctx.user.id, self.command_categories)
        
        # Add footer with command count
        command_count = len(self.bot.application_commands) if hasattr(self.bot, 'application_commands') else 0
        embed.set_footer(text=f"{command_count} slash commands available • Use /help [command] for details")
        
        await ctx.followup.send(embed=embed, view=view)
    
    async def _show_command_help(self, ctx: Interaction, command_name: str):
        """Show detailed help for a specific command"""
        # Check if the input is a category
        command_name = command_name.lower()
        for category, _ in self.command_categories.items():
            if command_name == category.lower():
                return await self._show_category_commands(ctx, category)
        
        # Try to find the command
        command = None
        
        # Search app commands if available
        if hasattr(self.bot, 'application_commands'):
            for cmd in self.bot.application_commands:
                if cmd.name.lower() == command_name:
                    command = cmd
                    break
        
        # If command not found
        if not command:
            embed = Embed(
                title="Command Not Found",
                description=f"Command `{command_name}` not found. Use `/help` to see available commands.",
                color=Color.red()
            )
            await ctx.followup.send(embed=embed)
            return
        
        # Build command help embed
        embed = Embed(
            title=f"Command: /{command.name}",
            description=command.description or "No description available",
            color=Color.blue()
        )
        
        # Add usage examples
        usage = f"/{command.name}"
        
        # Add parameters if available
        if hasattr(command, 'parameters') and command.parameters:
            params_text = ""
            for param in command.parameters:
                param_type = param.type if hasattr(param, 'type') else "Unknown"
                required = " (required)" if hasattr(param, 'required') and param.required else " (optional)"
                params_text += f"`{param.name}`: {param.description or 'No description'} - Type: {param_type}{required}\n"
            
            if params_text:
                embed.add_field(name="Parameters", value=params_text, inline=False)
                
                # Update usage with parameters
                usage = f"/{command.name}"
                for param in command.parameters:
                    if hasattr(param, 'required') and param.required:
                        usage += f" <{param.name}>"
                    else:
                        usage += f" [{param.name}]"
        
        embed.add_field(name="Usage", value=f"```{usage}```", inline=False)
        
        # Add permission information if available
        permissions_required = "None"
        if hasattr(command, '_checks'):
            for check in command._checks:
                check_str = str(check)
                if "has_permissions" in check_str or "bot_has_permissions" in check_str or "is_owner" in check_str:
                    permissions_required = "Administrator or Bot Owner"
                    break
        
        embed.add_field(name="Required Permissions", value=permissions_required, inline=True)
        
        # Show if premium required
        premium_required = "No"
        if hasattr(command, 'premium_only') and command.premium_only:
            premium_required = "Yes"
        
        embed.add_field(name="Premium Required", value=premium_required, inline=True)
        
        # Add footer
        embed.set_footer(text="Use /help to see all command categories")
        
        await ctx.followup.send(embed=embed)
    
    async def _show_category_commands(self, ctx: Interaction, category: str):
        """Show commands in a specific category"""
        embed = Embed(
            title=f"{category} Commands",
            description=self.command_categories.get(category, ""),
            color=Color.blue()
        )
        
        # Filter commands by category
        commands_in_category = []
        if hasattr(self.bot, 'application_commands'):
            for cmd in self.bot.application_commands:
                # Check if command category matches
                cmd_category = getattr(cmd, 'category', None)
                if (cmd_category and cmd_category.lower() == category.lower()) or \
                   (cmd.name.lower().startswith(category.lower()) and not cmd_category):
                    commands_in_category.append(cmd)
        
        # Add commands to embed
        if commands_in_category:
            for cmd in commands_in_category:
                embed.add_field(
                    name=f"/{cmd.name}",
                    value=cmd.description or "No description",
                    inline=False
                )
        else:
            if embed.description:
                embed.description = embed.description + "\n\nNo commands found in this category."
            else:
                embed.description = "No commands found in this category."
        
        # Add footer
        embed.set_footer(text="Use /help [command] for detailed command information")
        
        await ctx.followup.send(embed=embed)
    
    class HelpView(View):
        """View with dropdown for help categories"""
        
        def __init__(self, bot, user_id: int, categories: Dict[str, str]):
            super().__init__(timeout=120)
            self.bot = bot
            self.user_id = user_id
            self.categories = categories
            
            # Add dropdown for categories
            self.add_item(self.CategorySelect(bot, user_id, categories))
        
        async def interaction_check(self, interaction: Interaction) -> bool:
            """Check if the user interacting is the one who invoked the command"""
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    "This help menu is not for you. Use `/help` to get your own menu.", 
                    ephemeral=True
                )
                return False
            return True
        
        async def on_timeout(self) -> None:
            """Called when the view times out"""
            # Disable all items when the view times out
            for item in self.children:
                item.disabled = True
            
            try:
                # Try to update the message with disabled items
                await self.message.edit(view=self)
            except:
                pass
        
        class CategorySelect(ui.Select):
            """Dropdown for selecting help categories"""
            
            def __init__(self, bot, user_id: int, categories: Dict[str, str]):
                self.bot = bot
                self.user_id = user_id
                
                # Create options for each category
                options = []
                # Add each category as an option
                for category, description in categories.items():
                    options.append(SelectOption(
                        label=category,
                        description=description[:100],  # Truncate if too long
                        value=category.lower()
                    ))
                
                super().__init__(
                    placeholder="Select a command category...",
                    min_values=1,
                    max_values=1,
                    options=options
                )
            
            async def callback(self, interaction: Interaction):
                """Handle selection of a category"""
                # Defer the response to avoid timeout
                await interaction.response.defer()
                
                selected_category = self.values[0]
                
                # Find the proper case for the category
                for category in self.view.categories.keys():
                    if category.lower() == selected_category:
                        selected_category = category
                        break
                
                # Show commands for the selected category
                embed = Embed(
                    title=f"{selected_category} Commands",
                    description=self.view.categories.get(selected_category, ""),
                    color=Color.blue()
                )
                
                # Filter commands by category
                commands_in_category = []
                if hasattr(self.bot, 'application_commands'):
                    for cmd in self.bot.application_commands:
                        # Check if command category matches
                        cmd_category = getattr(cmd, 'category', None)
                        if (cmd_category and cmd_category.lower() == selected_category.lower()) or \
                           (cmd.name.lower().startswith(selected_category.lower()) and not cmd_category):
                            commands_in_category.append(cmd)
                
                # Add commands to embed
                if commands_in_category:
                    for cmd in commands_in_category:
                        embed.add_field(
                            name=f"/{cmd.name}",
                            value=cmd.description or "No description",
                            inline=False
                        )
                else:
                    if embed.description:
                        embed.description = embed.description + "\n\nNo commands found in this category."
                    else:
                        embed.description = "No commands found in this category."
                
                # Add footer
                embed.set_footer(text="Use /help [command] for detailed command information")
                
                await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    """Set up the help cog"""
    await bot.add_cog(HelpCog(bot))
    logger.info("Help Fixed commands cog loaded")