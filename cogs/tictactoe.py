import discord
from discord.ext import commands
import random

PLAYER_X = '❌'
PLAYER_O = '⭕'
EMPTY = '\u200b'

class TicTacToeView(discord.ui.View):
    def __init__(self, bot, board = None):
        super().__init__()
        self.bot = bot
        if board is None:
            for i in range(3):
                for j in range(3):
                    button = TicTacToeButton(i, j)
                    self.add_item(button)
        else:
            for i in range(3):
                for j in range(3):
                    button = TicTacToeButton(i, j)
                    button.label = board[i][j] if board[i][j] != EMPTY else '\u200b'
                    button.disabled = board[i][j] != EMPTY
                    self.add_item(button)

class TicTacToeButton(discord.ui.Button):
    def __init__(self, row, col):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=row)
        self.row = row
        self.col = col

    async def callback(self, interaction: discord.Interaction):
        game = self.view.bot.get_cog("TicTacToe")
        if game.ctx.author != interaction.user:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        if game.game_over:
            await interaction.response.send_message("The game is already over!", ephemeral=True)
            return
        if game.board[self.row][self.col] != EMPTY:
            await interaction.response.send_message("Invalid move!", ephemeral=True)
            return
        game.board[self.row][self.col] = game.current_player
        self.label = game.current_player
        self.disabled = True
        await interaction.response.edit_message(view=self.view)
        if game.check_winner(game.current_player):
            await game.end_game(f"{game.current_player} wins!", interaction)
            return
        if game.is_board_full():
            await game.end_game("It's a tie!", interaction)
            return
        await game.switch_player(interaction)
        if game.current_player == PLAYER_O:
            await game.ai_move(interaction)

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.board = [[EMPTY for _ in range(3)] for _ in range(3)]
        self.current_player = None
        self.game_over = False
        self.ctx = None
        self.game_running = False

    @commands.slash_command(name="play", description="Play Tic Tac Toe against an AI.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def play(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.board = [[EMPTY for _ in range(3)] for _ in range(3)]
        self.current_player = random.choice([PLAYER_X, PLAYER_O])
        self.game_over = False
        if not self.game_running:
            self.game_running = True
            view = TicTacToeView(self.bot)
            await ctx.respond(content=self.current_player + "'s turn!", view=view)
            if self.current_player == PLAYER_O:
                await self.ai_move(view)
        else:
            await ctx.respond(content="There is already a game running, please hold while we figure a fix!", ephemeral=True)

    def check_winner(self, player):
        for i in range(3):
            if all(self.board[i][j] == player for j in range(3)) or all(self.board[j][i] == player for j in range(3)):
                return True
        if all(self.board[i][i] == player for i in range(3)) or all(self.board[i][2-i] == player for i in range(3)):
            return True
        return False

    def is_board_full(self):
        return all(self.board[row][col] != EMPTY for row in range(3) for col in range(3))

    async def switch_player(self, interaction: discord.Interaction):
        # Check if there is a winner
        if self.check_winner(self.current_player):
            self.game_over = True
            if self.current_player == PLAYER_X:
                await self.end_game("You win, contact Otto to claim a prize you cheater!",interaction)
            else:
                await self.end_game(f"{self.current_player} wins!", interaction)
            return
        else:
            self.current_player = PLAYER_X if self.current_player == PLAYER_O else PLAYER_O

    async def end_game(self, message, interaction: discord.Interaction):
        view = TicTacToeView(self.bot, self.board)
        for row in interaction.message.components:
            for child in row.children:
                child.disabled = True
        self.game_over = True
        await interaction.edit_original_response(content=message, view=view)

    async def ai_move(self, interaction: discord.Interaction):
        best_move = self.find_best_move()
        if best_move:
            self.board[best_move[0]][best_move[1]] = PLAYER_O
            await self.switch_player(interaction)
            # Use edit_original_response to update the message and the view
        if not self.game_over:
            await interaction.message.edit(content=self.current_player + "'s turn", view=TicTacToeView(self.bot, self.board))

    def create_view(self):
        # Recreate the view based on the current state of the game
        view = TicTacToeView(self.bot)
        for i in range(3):
            for j in range(3):
                button = TicTacToeButton(i, j)
                button.label = self.board[i][j] if self.board[i][j] != EMPTY else EMPTY
                button.disabled = self.board[i][j] != EMPTY
                view.add_item(button)
        return view

    def find_best_move(self):
        best_score = -float('inf')
        move = None
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == EMPTY:
                    self.board[i][j] = PLAYER_O
                    score = self.minimax(False)
                    self.board[i][j] = EMPTY
                    if score > best_score:
                        best_score = score
                        move = (i, j)
        return move

    def minimax(self, is_maximizing):
        if self.check_winner(PLAYER_O):
            return 1
        elif self.check_winner(PLAYER_X):
            return -1
        elif self.is_board_full():
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == EMPTY:
                        self.board[i][j] = PLAYER_O
                        score = self.minimax(False)
                        self.board[i][j] = EMPTY
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == EMPTY:
                        self.board[i][j] = PLAYER_X
                        score = self.minimax(True)
                        self.board[i][j] = EMPTY
                        best_score = min(score, best_score)
            return best_score

    @play.error
    async def play_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.CommandOnCooldown):
            time = round(error.retry_after)
            await ctx.respond(content=f"Please wait {time} seconds before starting another game!", ephemeral=True)

def setup(bot):
    bot.add_cog(TicTacToe(bot))
