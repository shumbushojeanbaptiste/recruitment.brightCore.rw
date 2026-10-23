type ApiErrorBody = {
  error?: {
    message?: unknown;
    details?: unknown;
  };
  meta?: {
    request_id?: unknown;
  };
};

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return typeof value === "object" && value !== null && "error" in value;
}

export function apiErrorMessage(
  payload: unknown,
  status: number,
  fallback = `Request failed (HTTP ${status}).`,
): string {
  if (!isApiErrorBody(payload) || !payload.error) return fallback;

  const { message, details } = payload.error;
  if (typeof message === "string" && message) {
    if (
      message === "Request validation failed." &&
      Array.isArray(details)
    ) {
      const messages = details.flatMap((detail) => {
        if (
          typeof detail === "object" &&
          detail !== null &&
          "message" in detail &&
          typeof detail.message === "string"
        ) {
          return [detail.message];
        }
        return [];
      });

      if (messages.length > 0) return messages.join("; ");
    }

    return message;
  }

  return fallback;
}
