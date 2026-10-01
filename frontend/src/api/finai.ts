const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type ChatRequest = {
  message: string;
  session_id?: string;
  language?: string;
  persona?: string;
  generate_response?: boolean;
  max_new_tokens?: number;
};

export async function sendChat(
  request: ChatRequest,
) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    const text = await response.text();

    throw new Error(
      `FinAI API error ${response.status}: ${text}`,
    );
  }

  return response.json();
}
