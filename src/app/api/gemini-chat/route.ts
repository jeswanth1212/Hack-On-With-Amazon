import { NextRequest, NextResponse } from 'next/server';

const GEMINI_API_KEY = 'AIzaSyDlEvkt7HM4ay72OuRXhUCPxh_BkQaA0PE';
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=' + GEMINI_API_KEY;

const SYSTEM_PROMPT = `You are Alexa, a friendly, knowledgeable movie and TV assistant for this web-based movie recommendation app.\n\nYou can:\n- Recommend movies and shows based on mood, genre, time, or user history\n- Answer questions about movies, actors, genres, and plots\n- Help users navigate THIS app's UI (navbar, search bar, friends tab, home page, etc.)\n- Give step-by-step instructions for using features as they appear in this app (e.g., how to add friends, use the search bar, view recommendations, etc.)\n- Offer social features (what friends are watching, how to invite, etc.)\n- Troubleshoot common issues\n- Share fun movie facts and trivia\n\nAlways be concise, helpful, and conversational. When giving help, refer to the actual UI elements and navigation of this app, not Fire TV or remote controls. If a user asks for a recommendation, suggest a few options and offer to show more. If they ask for help, guide them step by step using the app's interface. If you don't know something, say so cheerfully.`;

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json();
    if (!Array.isArray(messages)) {
      return NextResponse.json({ error: 'Invalid messages' }, { status: 400 });
    }
    // Prepend system prompt
    const geminiMessages = [
      { role: 'user', content: SYSTEM_PROMPT },
      ...messages,
    ];
    const body = {
      contents: [
        {
          role: 'user',
          parts: geminiMessages.map(m => ({ text: m.content })),
        },
      ],
    };
    const response = await fetch(GEMINI_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.text();
      return NextResponse.json({ error: err }, { status: 500 });
    }
    const data = await response.json();
    // Gemini's response is in data.candidates[0].content.parts[0].text
    const reply = data?.candidates?.[0]?.content?.parts?.[0]?.text || 'Sorry, I could not generate a reply.';
    return NextResponse.json({ reply });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Unknown error' }, { status: 500 });
  }
} 