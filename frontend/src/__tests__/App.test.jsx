import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../app/App";

const mockFetchBackendHealth = vi.fn();
const mockFetchModelStats = vi.fn();
const mockPredictNews = vi.fn();
const mockExtractErrorMessage = vi.fn((error) => error.message || "Request failed");

vi.mock("../api/client", () => ({
  fetchBackendHealth: (...args) => mockFetchBackendHealth(...args),
  fetchModelStats: (...args) => mockFetchModelStats(...args),
  predictNews: (...args) => mockPredictNews(...args),
  extractErrorMessage: (...args) => mockExtractErrorMessage(...args),
}));

function renderApp(initialEntries = ["/"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <App />
    </MemoryRouter>
  );
}

describe("App", () => {
  beforeEach(() => {
    mockFetchBackendHealth.mockResolvedValue({
      status: "ok",
      startup_error: null,
    });
    mockFetchModelStats.mockResolvedValue({
      deployed_model: "RandomForest",
      models: {},
    });
    mockPredictNews.mockResolvedValue({
      prediction_id: "pred-1",
      prediction: "REAL",
      confidence: 0.91,
      model: "RandomForest",
      explanation: {
        top_tfidf_features: [],
        explanation_method: "importance_weighted_tfidf",
        credibility_score: null,
        text_statistics: {
          text_length: 54,
          punctuation_count: 0,
          all_caps_ratio: 0,
          exclamation_count: 0,
        },
      },
    });
    mockExtractErrorMessage.mockImplementation((error) => error.message || "Request failed");
  });

  it("loads the page and shows the main headline", async () => {
    renderApp();

    expect(await screen.findByRole("heading", { name: "IS IT REAL?" })).toBeInTheDocument();
  });

  it("disables the submit button when the textarea is empty", async () => {
    renderApp();

    const button = await screen.findByRole("button", { name: "Analyze" });
    expect(button).toBeDisabled();
  });

  it("updates the character counter as the user types", async () => {
    const user = userEvent.setup();
    renderApp();

    const textarea = await screen.findByPlaceholderText(/paste the statement/i);
    const text = "This is a test claim with enough characters.";
    await user.type(textarea, text);

    expect(screen.getByText(new RegExp(`${text.length} characters`, "i"))).toBeInTheDocument();
  });

  it("shows an error message instead of crashing when the API request fails", async () => {
    const user = userEvent.setup();
    mockPredictNews.mockRejectedValueOnce(new Error("Backend unavailable"));

    renderApp();

    const textarea = await screen.findByPlaceholderText(/paste the statement/i);
    await user.type(textarea, "This is a sufficiently long fake news claim.");
    await user.click(screen.getByRole("button", { name: "Analyze" }));

    await waitFor(() => {
      expect(screen.getByText("Backend unavailable")).toBeInTheDocument();
    });
  });
});
