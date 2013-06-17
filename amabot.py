import praw # Gotta use 2.7 for this
import time
from settings import * # Allows variables from settings.py to be used without a prefix

# Formats text to create a row for the table that is usable
def makeRow(post, reply): #Need to link username to question
    return  post.author.name+" | "+post.body.replace('\n', ' ')+" | "+reply.body.replace('\n', ' ')+" \n"
    
def postTable(parentToPostTo, text):
    # Start Building the Table
    header = "Problem with the Bot? Reply to the post and I'll see it!\n\nUser: | Comment: | Answer: \n :--: | :--: | :--: \n"
    table = header+text

    if isinstance(parentToPostTo, praw.objects.Comment): # Comments have a different reply method in praw
        if PostMultipleComments: # Only post if the flag is set. The if is nested so that we still absorb the comment instance and don't accidentally call a function that we can't in the else clause.
            return parentToPostTo.reply(table)
    else: 
        return parentToPostTo.add_comment(table)
    
def isGoodSubmission(submission):
    if debug: print('Checking if "'+submission.title+'" is a good post to table')
    if submission.score < SCORE_THRESHOLD: # If the submission score is too low, we ignore it
        if debug: print('--Failed the score test\n')
        return False
    
    difference = time.time() - submission.created_utc
    if difference > 8*60*60 or difference < 1*60*60: # If the submission is over 8 hours old or if it's under an hour old
        if debug: print('--Failed the time test\n')
        return False
    
    if debug: print("++It's good!\n")
    return True

# Main Function that scrapes the AMA and builds a table as a reply
def goBotGo(AMA):
    # The id of the AMAer
    AMAUsername = AMA.author
    text = ''

    # Used as the thing to post a reply to
    previousTable = AMA
    
    if debug: print('++Started on AMA')
    
    try:
        for post in AMA.comments: # This goes through the top level posts one by one
            if post.id not in already_done:
                try:
                    for reply in post.replies:
                        if reply.author == AMAUsername: # If the AMAer replied, add it to the table
                            row = makeRow(post, reply)
                            if len(text)+len(row) > 9900: # If the table has gotten too large, post what we have and continue
                                previousTable = postTable(previousTable, text)
                                text = '' # Restart the text
                            
                            text += row
                            already_done.append(post.id)
                except AttributeError as e:
                    if debug and showExceptions: print('Error: Out of Replies. Exception: ', e)
                
    except AttributeError as e:
        if debug and showExceptions: print('Error: Out of Posts. Exception:', e)

    # Finally, post the leftovers
    postTable(previousTable, text)


r = praw.Reddit(user_agent=USER_AGENT) #as per the request of the API rules
r.login(USERNAME, PASSWORD)

# List of comments I've handled already
already_done = []

# Main Loop Starts Here
while True:
    print('Started scraping /r/IAMA for posts to table\n')
    
    # Get the top submissions from r/IAMA
    AMAs = r.get_subreddit('IAmA').get_hot(limit=1) #CHANGE TO 10 WHEN DONE TESTING

    for AMA in AMAs:
        if isGoodSubmission(AMA):
            goBotGo(AMA)
            if debug: print('Finished working on "'+AMA.title+'"\n')
        time.sleep(SUBMISSION_DELAY) # Wait a bit in between each submission so I don't overload Reddit

    # Delay runs by an hour each
    print('Finished scraping /r/IAMA and posting. Waiting for next run...')
    time.sleep(RUN_DELAY)


