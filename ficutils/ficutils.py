# Adds fic-related utilities.
# LICENSE: This module is licenced under Apache License 2.0
# @category   Tools
# @copyright  Copyright (c) 2018-2020 ivy
# @version    1.0
# @author     ivy, redqwyll

import asyncio
import urllib
import requests
from bs4 import BeautifulSoup

from datetime import datetime
import re

from redbot.core import commands
from typing import Any

Cog: Any = getattr(commands, "Cog", object)


"""
Notes
 - Ao3
     Supports both fic links, 
     e.g. 'https://archiveofourown.org/works/18426930/chapters/43647630'
     and collection links, 
     e.g. 'https://archiveofourown.org/collections/Heliocentrism/works/20465864'
     
     If not a fic, an error is raised and an empty dict returned.
 - Download uses urllib due to its speed
     In the case of failure, it switches to using 'requests' library, which is slower but (experimentally) more robust
     
Todo
 - Invalid links?
 - Author links?
"""

# === Methods ===
# Download HTML
def download(url):
    """
    Parameters
    ----------
    url: str
        The URL to be downloaded
        
    Returns
    -------
    soup: BeautifulSoup
        BeautifulSoup representation of downloaded HTML page
    
    """
    # Preprocessing
    # If Ao3, append with '?view_adult=true' to bypass potential adult filter
    if 'archiveofourown.org' in url:
        url += '?view_adult=true'
    
    # Download raw HTML
    try: 
        fp = urllib.request.urlopen(url)
        mybytes = fp.read()
        html = mybytes.decode('utf-8')
        fp.close
    except:
        html = requests.get(url).content
    
    # Parse into BS4
    return BeautifulSoup(html, 'html.parser')

# Get metadata
def metadata(soup, website):
    """
    Parameters
    ----------
    soup: BeautifulSoup
        Page HTML
    website: str
        Ao3, FFN, etc. to filter between different formats 
        
    Returns
    -------
    metadata: dictionary
        {
            name: str 
            id: str 
            chapter: int 
            finished: str
            summary: str 
            published: int // (created_utc)
            updated: int // (created_utc) 
            author: []{} => [{name: str, id: str}] 
            relationships: str[] 
            category: str[] 
            character: str[] 
            freeform: str[] 
            rating: str 
            warnings: str[] 
            fandom: str[]
            words: int
            reviews: int // Ao3 - comments
            favs: int // Ao3 - bookmarks
        }
        
    Raises
    ------
    e: Exception
        Exception in case anything goes wrong
    """
    try:        
        json = {}

        # Website filter
        if (website == 'ao3'):
            # Ao3

            json = metadata_ao3(soup)

            return json
        elif (website == 'ffn'):
            # FFN
            
            json = metadata_ffn(soup)

            return json
        elif (website == 'fnp'):
            # FictionPress
            
            json = metadata_ffn(soup, 'fnp')

            return json
        
    except Exception as e:
        raise e


# === LIST OF METADATA() SUBMETHODS ===

def metadata_ao3(soup):
    """
    metadata() for Ao3
    
    '.find()' instead of '.find_all()' used because '.find_all()' will be used 
    in conjunction with '[0]' anyway
    
    Parameters
    ----------
    soup: BeautifulSoup
        The HTML page from which to extract results
        
    Returns
    -------
    result: dictionary
        Follows key-value pair as in metadata() 
    """
    result = {}
    
    # Populate metadata
    #--- name & id
    result['story_name'] = soup.find('h2', {'class' : 'title heading'}).getText().strip()
    result['sid'] = 'ao3-' + soup.find('dd', {'class' : 'bookmarks'}).find('a', href = True)['href'].split('/')[2]
    
    #--- chapter & finished
    chapters = soup.find('dd', {'class' : 'chapters'}).getText().split('/')
    current_chapters = chapters[0]
    max_chapters = chapters[1]
    
    result['chapter'] = int(current_chapters)
    result['finished'] = str(max_chapters)
    #result['finished'] = current_chapters == max_chapters
    
    #--- summary
    result['summary'] = soup.find('blockquote', {'class' : 'userstuff'}).getText().strip()
    
    #--- published
    result['published'] = datetime.strptime(soup.find('dd', {'class' : 'published'}).getText(), '%Y-%m-%d').timestamp()
    
    #--- updated
    # potentially unused if single chapter, in which case, get published
    last_date = soup.find('dd', {'class' : 'status'})
    
    if last_date is None: 
        last_date = soup.find('dd', {'class' : 'published'})
    
    last_date = datetime.strptime(last_date.getText(), '%Y-%m-%d').timestamp()
    
    result['updated'] = last_date
    
    #--- author
    authors_html = soup.find('h3', {'class' : 'byline heading'}).find_all('a', href = True)
    author_list = []
    
    for author in authors_html:
        author_list.append({
            'user_name' : author.getText(),
            'uid' : 'ao3-' + author['href'].split('/')[2]
        })
        
    result['author'] = author_list
    
    #--- relationships
    # potentially unused 
    relationships_list = []
    
    try:
        relationships_html = soup.find('dd', {'class' : 'relationship tags'}).find_all('li')

        for rel in relationships_html:
            relationships_list.append(rel.getText())
    except AttributeError:
        "" # Do nothing
    
    result['relationships'] = relationships_list
    
    #--- category
    # potentially unused 
    category_list = []
    
    try:
        category_html = soup.find('dd', {'class' : 'category tags'}).find_all('li')

        for rel in category_html:
            category_list.append(rel.getText())
    except AttributeError:
        "" # Do nothing
    
    result['category'] = category_list
    
    #--- character
    # potentially unused 
    character_list = []
    
    try:
        character_html = soup.find('dd', {'class' : 'character tags'}).find_all('li')

        for rel in character_html:
            character_list.append(rel.getText())
    except AttributeError:
        "" # Do nothing
    
    result['character'] = character_list
    
    #--- freeform
    # potentially unused 
    freeform_list = []
    
    try:
        freeform_html = soup.find('dd', {'class' : 'freeform tags'}).find_all('li')

        for rel in freeform_html:
            freeform_list.append(rel.getText())
    except AttributeError:
        "" # Do nothing
    
    result['freeform'] = freeform_list
    
    """     #--- tags
    # potentiall unused
    tags_list = []
    
    for html_class in ['category', 'character', 'freeform']:
        try:
            tags = soup.find('dd', {'class' : html_class + ' tags'}).find_all('li')

            for t in tags:
                tags_list.append(t.getText())
        except AttributeError:
            continue # If a particular html_class is unused, go to the next one
        
    result['tags'] = tags_list """
    
    #--- fandom
    # potentially unused
    fandom_list = []
    
    try:
        fandom_html = soup.find('dd', {'class' : 'fandom tags'}).find_all('li')
        
        for t in fandom_html:
            fandom = t.getText()
            if " | " in fandom:
                fandom = fandom.split(" | ")[1]
            fandom_list.append(fandom)
    except AttributeError:
        "" # do nothing
        
    result['fandom'] = fandom_list
    
    #--- rating
    result['rating'] = soup.find('dd', {'class' : 'rating tags'}).getText().strip()
    
    #--- warning
    # potentiall unused 
    warnings_list = []
    
    try: 
        warnings_html = soup.find('dd', {'class' : 'warning tags'}).find_all('li')

        for warn in warnings_html:
            warnings_list.append(warn.getText())
    except AttributeError:
        "" # do nothing
    
    result['warnings'] = warnings_list
    
    #--- words
    num_words = soup.find('dd', {'class' : 'words'})
    
    num_words = int(num_words.getText())
    
    result['words'] = num_words
    
    #--- reviews
    # untested but potentially unused if 0, requires confirmation
    num_reviews = soup.find('dd', {'class' : 'comments'})
    
    if num_reviews is None: 
        num_reviews = 0
    else: 
        num_reviews = num_reviews.getText()
    
    result['reviews'] = num_reviews
    
    #--- favourites
    # untested but potentially unused if 0, requires confirmation
    num_fav = soup.find('dd', {'class' : 'bookmarks'})
    
    if num_fav is None: 
        num_fav = 0
    else: 
        num_fav = num_fav.getText()
    
    result['favs'] = num_fav
    
    return result

def metadata_ffn(soup, site: str = 'ffn'):
    """
    metadata() for FFN
    
    Unsure if this works for fics posted under an hour ago due to published key.
    Crossovers supported
    Follows not recorded
    
    Parameters
    ----------
    soup: BeautifulSoup
        The HTML page from which to extract results
    site: str
        The website (defaults to ffn)
        
    Returns
    -------
    result: dictionary
        Follows key-value pair as in metadata() 
    """
    result = {}
    
    # Populate metadata
    # --- name & id
    result['story_name'] = soup.find('b', { 'class' : 'xcontrast_txt' }).getText()
    result['sid'] = site + '-' + soup.find('link', { 'rel' : 'canonical' }, href = True)['href'].split('/')[-3]
    
    # --- Get mishmash from FFN
    mishmash = soup.find('span', { 'class' : 'xgray xcontrast_txt' }).getText()
    
    # --- chapter
    try:
        # 1-chapter fics have no 'Chapters: \d'
        chapters, mishmash = regex_extract('Chapters: ', '\d+', mishmash)
        
        chapters = int(chapters)
    except: 
        chapters = 1
        
    result['chapter'] = chapters
    
    # --- finished
    try:
        # Incomplete fics don't have Status: Complete
        finished, mishmash = regex_extract('Status: ', 'Complete', mishmash)
    except: 
        finished = None
        
    #result['finished'] = finished == 'Complete'
    if finished == 'Complete':
        result['finished'] = str(chapters)
    else:
        result['finished'] = "?"
    
    # --- summary
    summary = soup.find('div', { 'style' : 'margin-top:2px' }).getText()
    
    result['summary'] = summary
    
    # --- published
    published, mishmash = regex_extract('Published: ', '[\w\s/]+', mishmash)
    published = published.strip()
    published = ffn_date_parser(published)
    
    result['published'] = published
    
    # --- updated
    # if there is only 1 chapter, equal to publish date
    #if result['chapter'] == 1:
    #    updated = published
    try: 
        updated, mishmash = regex_extract('Updated: ', '[\w\s/]+', mishmash)
        updated = updated.strip()
        updated = ffn_date_parser(updated)
    except:
        updated = published
        
    result['updated'] = updated
    
    # --- author
    # FFN only permits one author
    xc_mm = soup.find_all('a', { 'class' : 'xcontrast_txt'}, href = True) # x_contrast mishmash
    
    # Get user from xc_mm
    for x in xc_mm:
        if '/u/' in x['href']:
            author = x.getText()
            author_id = site + '-' + x['href'].split('/')[2]
    
    result['author'] = [{
        'user_name' : author,
        'uid' : author_id
    }]
    
    # --- relationships
    # None '[]' relationships added below
    result['relationships'] = []
#     try:
#         rels, mishmash = regex_extract('', '\[[\w\s\.,]+\]', mishmash)
        
# #         rels = re.search('\[[\w\s\.,]+\]', mishmash).group()
#     except:
#         rels = []
    
#     result['relationships'] = rels
    
    # --- tags 
    # handled below
    
    # --- rating
    rating, mishmash = regex_extract('Rated: Fiction', '\s+[\w\+]+', mishmash)
    
    result['rating'] = rating
    
    # --- warnings
    # No warnings
    result['warnings'] = []
    
    # --- fandom
    fandom = soup.find('div', { 'id' : 'pre_story_links'} ).find('span').find_all('a')
    
    fandom_final = []
    
    for i in range(len(fandom)):
        # Get text from soup
        fandom[i] = fandom[i].getText()
        
        # For crossover situations, break up the fandoms
        if 'Crossover' in fandom[i]:
            fandom_final.extend(fandom[i].replace(' Crossover', '').split(' + '))
        else:
            fandom_final.append(fandom[i])
    
    result['fandom'] = fandom_final
    
    # --- words
    words, mishmash = regex_extract('Words: ', '[\d,]+', mishmash)
    words = words.replace(',', '')
    
    result['words'] = int(words)
    
    # --- reviews
    try:
        reviews, mishmash = regex_extract('Reviews: ', '[\d,]+', mishmash)
        reviews = reviews.replace(',', '')
    except:
        reviews = 0
    
    result['reviews'] = int(reviews)
    
    # --- favourites
    try: 
        favs, mishmash = regex_extract('Favs: ', '[\d,]+', mishmash)
        favs = favs.replace(',', '')
    except:
        favs = 0
        
    result['favs'] = int(favs)
    
    # --= tags
    # We take everything that is not covered by the other tags, including relationships
    # We remove 'Follows' and 'id'
    for regexes in [
        ['Follows: ', '[\d,]+'],
        ['id: ', '\d+']
    ]: 
        try: 
            mishmash = regex_extract(regexes[0], regexes[1], mishmash)[1]
        except:
            continue

    tags = re.split('\s+-\s+', mishmash)
    tags = filter(lambda x : x.strip() not in ['', '-'], tags)
    tags = list(tags)
    
    # Experimental adding of 'last' (index 2) tags to to relationships
    if len(tags) > 2:
        try:
            rels = tags[2]
            rels = rels.split(',')
            
            tags = tags[0:2]
            
    #         rels = re.split(r'[,\\]', tags[2])
            result['relationships'] = rels
    #         tags = tags[0:2]
        except Exception as e:
            print(e.msg)
    else:
        result['relationships'] = []
    
    result['freeform'] = tags
    # category and character tags do not exist in ffn
    result['character'] = []
    result['category'] = []
    
#     result['rem'] = mishmash
    
    return result
    
    """
    name: str 
    id: str 
    chapter: int 
    finished: bool 
    summary: str 
    published: int // (created_utc)
    updated: int // (created_utc) 
    author: []{} => [{name: str, id: str}] 
    relationships: str[] 
    tags: str[] 
    rating: str 
    warnings: str[] 
    fandom: str[]
    words: int
    reviews: int // Ao3 - comments
    favs: int // Ao3 - bookmarks
    """

def ffn_date_parser(string):
    """
    Used to parse dates from FF.net
    
    Parameters
    -------
    string: str
        The string containing the date to be parsed
        Includes the key, e.g. Published: X or Updated: Y
        
    Returns
    -------
    result: int
        The UTC timestamp
        
    """
    # The following standardises the date to Month / Day / Year so it can be further converted later
    if re.search('\d+/\d+/\d+', string) is not None: 
        # Date format is X/X/X
        result = string
    elif re.search('\d+/\d+', string) is not None:
        # Date format is month/day
        
        # Ensure month and day are zero padded
        md = string.split('/') # month_day
        
        for i in [0, 1]: 
            if len(md[i]) < 2:
                md[i] = '0' + md[i]
        
        result = md[0] + '/' + md[1]
        
        # Add year at the back
        result += '/' + str(datetime.now().year)
    elif re.search('\d+\w+', string) is not None:
        # Date format is '8h ago'
        now = datetime.now()
        result = str(now.month) + '/' + str(now.day) + '/' + str(now.year)
    
    result = datetime.strptime(result, '%m/%d/%Y').timestamp()
    
    return result

def regex_extract(pre, exp, string):
    """
    Extracts the expression exp from the string, if it is preceded by pre
    The difference from a re.search() is that it deletes whatever is returned after searching
    We need this to slowly sift through FFN's tags
    
    Parameters
    =======
    pre: str
        The expression that precedes our desired expression
        If it is empty, this is not used
    exp: str
        The regex to be extracted
    string: str
        The string from which this is to be extracted
        
    Returns
    ======
    
    """
    regex = exp
    
    if pre != '':
        regex = '(?<=' + pre + ')' + regex
        
    regex_clean = pre + exp
        
    result = re.search(regex, string).group().strip()
    
    remainder = re.sub(regex_clean, '', string)
    
    return result, remainder


def fic_data(link, website = None):
    """
    Returns a JSON representation of the fic's metadata
    
    Parameters
    ----------
    link: str
        URL of the fic to be recced
    website: str
        Host, e.g. ao3, ffn
        If none, the method attempts to figure it out
        
    Returns
    -------
    result: dictionary
        dictionary containing metadata    
    """
    soup = download(link)
    
    result = {}

    try:
        # Determine website
        if website is None:
            if 'archiveofourown.org' in link:
                website = 'ao3'
            elif 'fanfiction.net' in link:
                website = 'ffn'
            else:
                raise ValueError('Unknown website.')

        return metadata(soup, website)
    except Exception as e:
        print('Error: ', e)
        print('Link: ', link)

def fic_rec(link: str, website: str = None):
    """
    Returns a JSON representation of the fic's metadata
    
    Parameters
    ----------
    link: str
        URL of the fic to be recced
    website: str
        Host, e.g. ao3, ffn
        If none, the method attempts to figure it out
        
    Returns
    -------
    result: dictionary
        dictionary containing metadata    
    """
    rec = ""

    try:
        if website is None:
            if 'archiveofourown.org' in link:
                website = 'ao3'
            elif 'fanfiction.net' in link:
                website = 'ffn'
            else:
                raise ValueError('Unknown website.')
        data = fic_data(link, website)

        if data['sid'][:3] == 'ao3':
            clean_link = "https://archiveofourown.org/works/" + data['sid'][4:]
        if data['sid'][:3] == 'ffn':
            clean_link = "https://fanfiction.net/s/" + data['sid'][4:]

        # process lists into strings
        authors = ", ".join(author['user_name'] for author in data['author'])
        if len(data['fandom']) > 0:
            fandoms = ", ".join(i for i in data['fandom'])
        else:
            fandoms = "None"
        if len(data['warnings']) > 0:
            warnings = ", ".join(i for i in data['warnings'])
        else:
            warnings = "Unknown"
        if len(data['relationships']) > 0:
            relationships = ", ".join(i for i in data['relationships'])
        else:
            relationships = "None"
        if len(data['character']) > 0:
            characters = ", ".join(i for i in data['character'])
        else:
            characters = "None"
        if len(data['category']) > 0:
            category = ", ".join(i for i in data['category'])
        else:
            category = "N/A"
        if len(data['freeform']) > 0:
            freeform = ", ".join(i for i in data['freeform'])
        else:
            freeform = "None"
        rec = f"**{data['story_name']}** ({clean_link}) by **{authors}**\n"
        rec += f"**Fandoms:** {fandoms}\n"
        rec += f"**Rating:** {data['rating']}    "
        if data['sid'][:3] == 'ao3':
            rec += f"**Category**: {category}    "
        rec += f"**Warnings:** {warnings}\n"
        rec += f"**Relationships:** {relationships}\n"
        if data['sid'][:3] == 'ao3':
            rec += f"**Characters:** {characters}\n"
        rec += f"**Tags:** {freeform}\n"
        rec += f"**Summary:** {data['summary']}\n"
        rec += f"**Words:** {data['words']}  "
        rec += f"**Chapters:** {data['chapter']}/{data['finished']}  "
        rec += f"**Kudos:** {data['favs']}  "
        rec += f"**Posted:** {(str(datetime.fromtimestamp(data['published']))[:10])}"
        if data['published'] != data['updated']:
            rec += f"  **Updated:** {(str(datetime.fromtimestamp(data['updated']))[:10])}"
        return rec
        
    except Exception as e:
        print('Error: ', e)
        print('Link: ', link)

def sid_parse(sid: str):
    """
    Returns a text summary of the fic's metadata given id + site
    
    Parameters
    ----------
    id: int
        ID of the fic to be recced
    website: str
        Host, e.g. ao3, ffn
        If none, the method fails
        
    Returns
    -------
    rec: str
        metadata summary  
    """
    website = sid[:3]
    story = sid[4:]

    try:
        if website == 'ao3':
            return f"https://archiveofourown.org/works/{story}/?view_adult=true"
        elif website == 'ffn':
            return f"https://fanfiction.net/s/{story}"
        elif website == 'fnp':
            return f"https://fictionpress.com/s/{story}"
        else:
            raise ValueError('Invalid website specified.')
    except Exception as e:
        logging.exception(link)


class Ficutils(Cog):
    """Fic-related utilities."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def rec(self, ctx, link: str):
        """Prints out an autogenerated recommendation summary for a linked fic."""
        await ctx.send(fic_rec(link))

    @commands.command(pass_context=True)
    async def rec_ao3(self, ctx, id: int):
        """Prints out an autogenerated recommendation summary for fic with AO3 id."""
        await ctx.send(fic_rec(sid_parse(f"ao3-{id}"), 'ao3'))

    @commands.command(pass_context=True)
    async def rec_ffn(self, ctx, id: int):
        """Prints out an autogenerated recommendation summary for fic with FFN id."""
        await ctx.send(fic_rec(sid_parse(f"ffn-{id}"), 'ffn'))

    @commands.command(pass_context=True)
    async def rec_fnp(self, ctx, id: int):
        """Prints out an autogenerated recommendation summary for fic with FNP id."""
        await ctx.send(fic_rec(sid_parse(f"fnp-{id}"), 'fnp'))
