import { NextResponse } from 'next/server';
import { AccessToken } from 'livekit-server-sdk';

// Forces the code to not be cached, so we get a new token every time
export const revalidate = 0;

export async function POST(req: Request) {
  // 1. Get keys from environment
  const API_KEY = process.env.LIVEKIT_API_KEY;
  const API_SECRET = process.env.LIVEKIT_API_SECRET;
  const LIVEKIT_URL = "wss://voice-agent-02t0q3nc.livekit.cloud";

  if (!API_KEY || !API_SECRET || !LIVEKIT_URL) {
    return NextResponse.json({ error: "Server misconfigured" }, { status: 500 });
  }

  try {
    // 2. Hardcode the room name so your Python Agent can find it easily
    const roomName = "test-room-22";
    
    // 3. Generate a random username for the human user
    const participantName = "User-" + Math.floor(Math.random() * 1000);
    const participantIdentity = "user_identity_" + Math.floor(Math.random() * 1000);

    // 4. Create the Token
    const at = new AccessToken(API_KEY, API_SECRET, {
      identity: participantIdentity,
      name: participantName,
      ttl: '15m', // Token valid for 15 minutes
    });

    // 5. Give permissions to join and talk
    at.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,   // Allow microphone
      canSubscribe: true, // Allow listening to bot
    });

    const token = await at.toJwt();

    // 6. Return the details to the frontend
    return NextResponse.json({
      serverUrl: LIVEKIT_URL,
      roomName: roomName,
      participantToken: token,
      participantName: participantName,
    });

  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: "Failed to generate token" }, { status: 500 });
  }
}