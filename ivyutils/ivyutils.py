# Adds core commands formerly from Bulbaspot. This adds utility commands.
# LICENSE: This module is licenced under Apache License 2.0
# @category   Tools
# @copyright  Copyright (c) 2018-2019 ivy
# @version    1.2
# @author     ivy

import asyncio

from redbot.core import commands

Cog: Any = getattr(commands, "Cog", object)


def decToHex(dec: int):
    """Converts a decimal integer to a hex string."""
    hexDigits = "0123456789ABCDEF"
    conversion = ''	# (Re-)initiate string
    # dec referenced as division

    # special case if dec is already 0
    if dec == 0:
        return "00"

    while dec != 0:
        remainder = dec % 16
        dec = dec // 16
        conversion += hexDigits[remainder]
    conversion = reverseString(conversion)

    return conversion


def reverseString(string: str):
    """Reverses a string."""
    return string[::-1]


def calcDeltaHex(n: float, rate: float):	# n = semitone difference, rate = the initial samplerate of your sample in Hz
    """Deflemask SegaPCM Delta command calculator.
    n = semitone difference, rate = the initial samplerate of your sample in Hz"""
    a = 2**(1/12)		# a = 12-tones in an octave (see 'Frequency Table formula' for the 'equal tempered scale')
    fn = rate * (a**n)		# Calculates the freq of the note, in 'n' semitones away from original pitch

    delta = fn / (31250/255)		# 255 is FF in hex; the max value of 20xx
    delta = int(round(delta, 0))	# Rounds the delta value to 0 decimals
    return decToHex(delta)		# Converts delta value from decimal to hex


class Ivyutils(Cog):
    """Ivy's utility commands. Useful for chiptune stuff mostly."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description='Note: rounds speed and tempo if given tempo results in a non-integer speed.')
    async def amkspeed(self, ctx, tempo: float):
        """Calculates AddMusicK speed, given tempo in BPM."""
        try:
            if (tempo <= 0):
                raise ValueError("Error: Tempo must be positive.")
            amkspeed = tempo * 256 / 625
            amkspeedtest = amkspeed % 1
            if (amkspeedtest != 0):
                await ctx.send("The AMK speed is about {:.0f}. The yielded tempo is {:g} BPM.".format(int(round(amkspeed)), round(amkspeed) * 625 / 256))
            else:
                await ctx.send("The AMK speed is {:.0f}.".format(amkspeed))
        except ValueError as err:
            # Display error message to channel
            await ctx.send("{} Type ``?help amkspeed`` for proper usage.".format(err))

    @commands.command(description='Calculates clock speed based on first the desired tempo and then the tick speed.')
    async def clockspeed(self, ctx, tempo: float, speed: float):
        """Calculates clock rate, given tempo in BPM and speed in ticks per row/unit."""
        try:
            if (tempo <= 0):
                raise ValueError("Error: Tempo must be positive.")
            if (speed <= 0):
                raise ValueError("Error: Tick speed must be positive.")
            clockspeed = tempo * speed / 15
            await ctx.send("The clock speed is {:g} Hz.".format(clockspeed))
        except ValueError as err:
            # Display error message to channel
            await ctx.send("{} Type ``?help clockspeed`` for proper usage.".format(err))

    @commands.command(description='Calculates tick speed based on first the desired tempo and then the clock speed.')
    async def tickspeed(self, ctx, tempo: float, clock: float):
        """Calculates tick speed, given tempo in BPM and clock rate in Hz."""
        try:
            if (tempo <= 0):
                raise ValueError("Error: Tempo must be positive.")
            if (tempo <= 0):
                raise ValueError("Error: Clock speed must be positive.")
            tickspeed = 15 * clock / tempo
            # if the tickspeed is non-int it'll print past the period
            await ctx.send("The tick speed is {:g}.".format(tickspeed))
        except ValueError as err:
            # Display error message to channel
            await ctx.send("{} Type ``?help tickspeed`` for proper usage.".format(err))

    @commands.command(pass_context=True)
    async def deltapcm(self, ctx, semitone_change: float=0, rate: float=31250.0):
        """Deflemask SegaPCM Delta command calculator. Written by DeltaRazero.
        semitone_change = semitone difference, rate = the initial samplerate of your sample in Hz"""
        if (semitone_change == 0 and rate == 31250.0):
            await ctx.send("Type ``?help deltapcm`` to get usage information.")
            return
        elif (rate <= 0 or rate > 31250):
            await ctx.send("Sample rate needs to be between 1 Hz and 31250 Hz... Type ``?help deltapcm`` to get usage information.")
            return
        
        try:
            convertedHex = calcDeltaHex(semitone_change, rate)
        except OverflowError as err:
            await ctx.send("{} Type ``?help deltapcm`` for proper usage.".format(err))
        
        if (convertedHex == ""):		# Check if hex value smaller than 00 or over FF and report to user
            await ctx.send("ERROR: Underflow ! Type ``?help deltapcm`` to get usage information.")
        elif (len(convertedHex) > 2):    
            await ctx.send("ERROR: Overflow ! Type ``?help deltapcm`` to get usage information.")
        else:
            if (len(convertedHex) == 1):    # Check if value not less than 10 (in hex) and add 0 if so
                convertedHex = "0" + convertedHex
            await ctx.send("Your delta command is: ``20{}``".format(convertedHex))
