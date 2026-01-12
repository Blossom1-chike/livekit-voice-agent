"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  ControlBar,
  useTracks,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useEffect, useState } from "react";

export default function Home() {
  const [details, setDetails] = useState<{
    serverUrl: string;
    roomName: string;
    participantToken: string;
  } | null>(null);

  // 1. Get the token immediately on load
  useEffect(() => {
    (async () => {
      try {
        const response = await fetch("/api/token", { method: "POST" });
        const data = await response.json();
        setDetails(data);
      } catch (e) {
        console.error("Failed to connect:", e);
      }
    })();
  }, []);

  if (!details) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  // 2. Connect to LiveKit
  return (
    <LiveKitRoom
      video={false}
      audio={true}
      token={details.participantToken}
      serverUrl={details.serverUrl}
      data-lk-theme="default"
      style={{ height: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}
    >
      <h1 className="text-3xl font-bold mb-4">Voice Agent Test</h1>
      <p className="mb-8">Connected to: {details.roomName}</p>
      
      {/* This component plays the audio from the bot */}
      <RoomAudioRenderer />
      
      {/* The Microphone controls */}
      <ControlBar variation="minimal" controls={{ microphone: true }} />
    </LiveKitRoom>
  );
}