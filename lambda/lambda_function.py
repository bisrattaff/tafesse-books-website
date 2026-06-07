"""
Tafesse Books — Advanced Search Lambda
Uses only Python built-ins + boto3 (pre-installed in Lambda).
No external dependencies required — deploy as a single file.

Environment variables (set in Lambda console):
  ANTHROPIC_API_KEY  — your Anthropic API key
  S3_BUCKET_NAME     — your S3 bucket name (e.g. "tafessebooks.com")
  TEXT_PREFIX        — folder in S3 where .txt files live (e.g. "book-text/")
"""

import json
import os
import urllib.request
import urllib.error
import boto3

s3_client = boto3.client('s3')

BOOKS = {
    'ሳይንቲስቶች (Scientists)':                      'Scientistoch.txt',
    'የ ሃይማኖቶች ልዪነት (Differences Among Religions)': 'Ye_Haimanotoch_Liyunet.txt',
    'የኑክሊየር ሃይል (Nuclear Energy)':                'Ye_Nuclear_Hail.txt',
    'Pillars of Creation (English)':               'Pillars_Of_Creation_English.txt',
    'Les Piliers de la Création (French)':         'Pillars_Of_Creation_French.txt',
    'ሌሎች ዓለማት (Different Worlds)':                'Leloch_Alemat.txt',
    'የ ቼዝ ጥበብ (Mastering Chess)':                 'Ye_Chess_Tibeb.txt',
    'እንዴት ነው የሚሰራው (How Does It Work)':           'Endet_New_Yemiseraw.txt',
    'Reflection':                                  'Reflection.txt',
    'Chronology of the Universe':                  'Chronology_Of_The_Universe.txt',
    'If I Were Black American':                    'If_I_Were_Black_American.txt',
    'Life In Las Vegas':                           'Life_In_Las_Vegas.txt',
    'My Spiritual Life':                           'My_Spiritual_Life.txt',
    'Turtles All The Way':                         'Turtles_All_The_Way.txt',
    'All Religions Lead The Same Way':             'All_Religions_Lead_The_Same_Way.txt',
    'Whence Life and Consciousness':               'Whence_Life_And_Consciousness.txt',
    'My Encounter With Telepathy':                 'My_Encounter_With_Telepathy.txt',
}

BUCKET      = os.environ.get('S3_BUCKET_NAME', '')
TEXT_PREFIX = os.environ.get('TEXT_PREFIX', 'book-text/')
MAX_CHUNKS  = 6
CHUNK_CHARS = 600
TEXT_THRESHOLD = 50


def get_book_text(filename):
    try:
        obj = s3_client.get_object(Bucket=BUCKET, Key=TEXT_PREFIX + filename)
        return obj['Body'].read().decode('utf-8', errors='replace')
    except Exception:
        return ''


def find_relevant_passages(query):
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    if not query_words:
        return []

    all_chunks = []
    for title, filename in BOOKS.items():
        text = get_book_text(filename)
        if not text:
            continue

        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 40]
        chunk, chunk_len, chunks = [], 0, []
        for para in paragraphs:
            chunk.append(para)
            chunk_len += len(para)
            if chunk_len >= CHUNK_CHARS:
                chunks.append(' '.join(chunk))
                chunk, chunk_len = [], 0
        if chunk:
            chunks.append(' '.join(chunk))

        for c in chunks:
            c_lower = c.lower()
            score = sum(1 for w in query_words if w in c_lower)
            if score > 0:
                all_chunks.append({'title': title, 'passage': c, 'score': score})

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
    if passages:
        context = '\n\n---\n\n'.join(
            f"From \"{p['title']}\":\n{p['passage']}" for p in passages
        )
    else:
        context = 'No matching passages found in the indexed books.'

    prompt = (
        f'You are a helpful assistant for tafessebooks.com, the website of Ethiopian author Tafesse Muluneh.\n\n'
        f'A visitor asked: "{query}"\n\n'
        f'Relevant passages from the books:\n\n{context}\n\n'
        f'Answer the visitor\'s question based on these passages. Be concise (3-5 sentences). '
        f'If the passages don\'t fully answer the question, say so and suggest downloading the book. '
        f'Mention which book(s) the information comes from.'
    )

    payload = json.dumps({
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 500,
        'messages': [{'role': 'user', 'content': prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        method='POST'
    )
    req.add_header('Content-Type', 'application/json')
    req.add_header('x-api-key', os.environ['ANTHROPIC_API_KEY'])
    req.add_header('anthropic-version', '2023-06-01')

    with urllib.request.urlopen(req, timeout=25) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        return result['content'][0]['text']


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
    method = (event.get('requestContext') or {}).get('http', {}).get('method', '')
    if method == 'OPTIONS':
        return cors_response(200, '')

    try:
        body = json.loads(event.get('body') or '{}')
        query = (body.get('query') or '').strip()

        if len(query) < 3:
            return cors_response(400, {'error': 'Please enter a longer question.'})

        passages = find_relevant_passages(query)
        answer   = ask_claude(query, passages)
        sources  = list(dict.fromkeys(p['title'] for p in passages))

        return cors_response(200, {'answer': answer, 'sources': sources})

    except Exception as e:
        print(f'Error: {e}')
        return cors_response(500, {'error': 'Search failed. Please try again.'})
