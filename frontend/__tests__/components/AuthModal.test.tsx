import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AuthModal } from "../../components/AuthModal";
import * as api from "../../lib/api";

// Mock the API module
jest.mock("../../lib/api", () => ({
  login: jest.fn(),
  register: jest.fn(),
}));

// Mock the store
const mockSetAuth = jest.fn();
jest.mock("../../lib/store", () => ({
  useAuthStore: () => ({
    setAuth: mockSetAuth,
  }),
}));

describe("AuthModal", () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it("renders nothing when closed", () => {
    const { container } = render(
      <AuthModal isOpen={false} onClose={mockOnClose} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders login form by default", () => {
    render(<AuthModal isOpen={true} onClose={mockOnClose} />);

    expect(screen.getByText("Sign In")).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
  });

  it("switches to register mode when clicking create account", () => {
    render(<AuthModal isOpen={true} onClose={mockOnClose} />);

    fireEvent.click(screen.getByText("Create one"));

    expect(screen.getByText("Create Account")).toBeInTheDocument();
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
  });

  it("switches back to login mode", () => {
    render(<AuthModal isOpen={true} onClose={mockOnClose} />);

    fireEvent.click(screen.getByText("Create one"));
    fireEvent.click(screen.getByText("Sign in"));

    expect(screen.getByText("Sign In")).toBeInTheDocument();
  });

  it("calls login API on form submit", async () => {
    const mockUser = { id: 1, email: "test@example.com", name: "Test User" };
    (api.login as jest.Mock).mockResolvedValueOnce({
      token: "test-token",
      user: mockUser,
    });

    render(<AuthModal isOpen={true} onClose={mockOnClose} />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith("test@example.com", "password123");
    });

    await waitFor(() => {
      expect(mockSetAuth).toHaveBeenCalledWith("test-token", mockUser);
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it("calls register API then login on registration", async () => {
    const mockUser = { id: 1, email: "new@example.com", name: "New User" };
    (api.register as jest.Mock).mockResolvedValueOnce({});
    (api.login as jest.Mock).mockResolvedValueOnce({
      token: "new-token",
      user: mockUser,
    });

    render(<AuthModal isOpen={true} onClose={mockOnClose} />);

    fireEvent.click(screen.getByText("Create one"));

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "New User" },
    });
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "new@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });

    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(api.register).toHaveBeenCalledWith(
        "new@example.com",
        "New User",
        "password123",
        undefined
      );
    });

    await waitFor(() => {
      expect(api.login).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it("shows error on login failure", async () => {
    (api.login as jest.Mock).mockRejectedValueOnce({
      response: { data: { detail: "Invalid credentials" } },
    });

    render(<AuthModal isOpen={true} onClose={mockOnClose} />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "wrongpassword" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });

  it("closes when clicking close button", () => {
    render(<AuthModal isOpen={true} onClose={mockOnClose} />);

    fireEvent.click(screen.getByText("×"));

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("disables submit button while loading", async () => {
    (api.login as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    render(<AuthModal isOpen={true} onClose={mockOnClose} />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Please wait...")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /please wait/i })
      ).toBeDisabled();
    });
  });
});
