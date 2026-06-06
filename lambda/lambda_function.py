"""
Tafesse Books — Advanced Search Lambda
Receives a natural language query, finds relevant passages from book text
files stored in S3, then asks Claude to answer using those passages.

Environment variables (set in Lambda console):
  ANTHROPIC_API_KEY  — your Anthropic API key
  S3_BUCKET_NAME     — e.g. "tafessebooks.com" (your existing S3 bucket)
  TEXT_PREFIX        — e.g. "book-text/" (folder where .txt files are stored)
"""

import json
import os
import boto3
import anthropic

s3_client = boto3.client('s3')

# Book filenames in S3 (under TEXT_PREFIX folder)
# Key = display title shown to user, Value = .txt filename in S3
BOOKS = {
    'ሳይንቲስቶች (Scientists)':                     'Scientistoch.txt',
    'የ ሃይማኖቶች ልዪነት (Differences Among Religions)': 'Ye_Haimanotoch_Liyunet.txt',
    'የኑክሊየር ሃይል (Nuclear Energy)':               'Ye_Nuclear_Hail.txt',
    'Pillars of Creation (English)':              'Pillars_Of_Creation_English.txt',
    'Les Piliers de la Création (French)':        'Pillars_Of_Creation_French.txt',
    'ሌሎች ዓለማት (Different Worlds)':               'Leloch_Alemat.txt',
    'የ ቼዝ ጥበብ (Mastering Chess)':                'Ye_Chess_Tibeb.txt',
    'እንዴት ነው የሚሰራው (How Does It Work)':          'Endet_New_Yemiseraw.txt',
    'Reflection':                                 'Reflection.txt',
    'Chronology of the Universe':                 'Chronology_Of_The_Universe.txt',
    'If I Were Black American':                   'If_I_Were_Black_American.txt',
    'Life In Las Vegas':                          'Life_In_Las_Vegas.txt',
    'My Spiritual Life':                          'My_Spiritual_Life.txt',
    'Turtles All The Way':                        'Turtles_All_The_Way.txt',
    'All Religions Lead The Same Way':            'All_Religions_Lead_The_Same_Way.txt',
    'Whence Life and Consciousness':              'Whence_Life_And_Consciousness.txt',
    'My Encounter With Telepathy':                'My_Encounter_With_Telepathy.txt',
}

BUCKET      = os.environ.get('S3_BUCKET_NAME', '')
TEXT_PREFIX = os.environ.get('TEXT_PREFIX', 'book-text/')
MAX_CHUNKS  = 6      # max relevant passages sent to Claude
CHUNK_CHARS = 600    # approximate characters per passage chunk


def get_book_text(filename):
    """Fetch a book's text file from S3. Returns empty string on failure."""
    try:
        key = TEXT_PREFIX + filename
        obj = s3_client.get_object(Bucket=BUCKET, Key=key)
        return obj['Body'].read().decode('utf-8', errors='replace')
    except Exception:
        return ''


def score_chunk(chunk, query_words):
    """Count how many query words appear in a text chunk."""
    chunk_lower = chunk.lower()
    return sum(1 for w in query_words if w in chunk_lower)


def find_relevant_passages(query):
    """
    Search all books for passages relevant to the query.
    Returns a list of dicts: {title, passage, score}
    """
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    if not query_words:
        return []

    all_chunks = []

    for title, filename in BOOKS.items():
        text = get_book_text(filename)
        if not text:
            continue

        # Split into paragraphs, then group short ones into ~CHUNK_CHARS blocks
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 40]
        chunk, chunk_len = [], 0
        chunks = []
        for para in paragraphs:
            chunk.append(para)
            chunk_len += len(para)
            if chunk_len >= CHUNK_CHARS:
                chunks.append(' '.join(chunk))
                chunk, chunk_len = [], 0
        if chunk:
            chunks.append(' '.join(chunk))

        for c in chunks:
            sc = score_chunk(c, query_words)
            if sc > 0:
                all_chunks.append({'title': title, 'passage': c, 'score': sc})

    # Sort by relevance, deduplicate by title (keep best chunk per book)
    all_chunks.sort(key=lambda x: x['score'], reverse=True)
    seen, results = set(), []
    for item in all_chunks:
        if item['title'] not in seen:
            seen.add(item['title'])
            results.append(item)
        if len(results) >= MAX_CHUNKS:
            break

    return results


def ask_claude(query, passages):
    """Send query + passages to Claude and return the answer text."""
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    if passages:
        context = '\n\n---\n\n'.join(
            f"From \"{p['title']}\":\n{p['passage']}" for p in passages
        )
    else:
        context = 'No matching passages found in the indexed books.'

    prompt = f"""You are a helpful assistant for tafessebooks.com, the website of Ethiopian author Tafesse Muluneh.

A visitor asked: "{query}"

Relevant passages from Tafesse's books:

{context}

Answer the visitor's question based on these passages. Be concise (3–5 sentences max).
If the passages don't fully answer the question, say so briefly and suggest downloading the relevant book.
Always mention which book(s) the information comes from."""

    message = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=500,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return message.content[0].text


def cors_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
        },
        'body': body if isinstance(body, str) else json.dumps(body),
    }


def lambda_handler(event, context):
    # Handle CORS preflight
    method = (event.get('requestContext') or {}).get('http', {}).get('method', '')
    if method == 'OPTIONS':
        return cors_response(200, '')

    try:
        body = json.loads(event.get('body') or '{}')
        query = (body.get('query') or '').strip()

        if len(query) < 3:
            return cors_response(400, {'error': 'Please enter a longer question.'})

        passages  = find_relevant_passages(query)
        answer    = ask_claude(query, passages)
        sources   = list(dict.fromkeys(p['title'] for p in passages))  # ordered unique

        return cors_response(200, {'answer': answer, 'sources': sources})

    except anthropic.AuthenticationError:
        return cors_response(500, {'error': 'API key error — contact the site admin.'})
    except Exception as e:
        print(f'Error: {e}')
        return cors_response(500, {'error': 'Search failed. Please try again.'})
