import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { UploadQuoteForm } from "../../components/UploadQuoteForm";
import * as api from "../../lib/api";

// Mock the API module
jest.mock("../../lib/api", () => ({
  fetchTechnologies: jest.fn(),
  fetchMaterials: jest.fn(),
  fetchProfiles: jest.fn(),
  uploadModel: jest.fn(),
  createQuote: jest.fn(),
  getAsset: jest.fn(),
}));

// Mock the store
let mockIsAuthenticated = false;
const mockAddItem = jest.fn();

jest.mock("../../lib/store", () => ({
  useAuthStore: () => ({
    isAuthenticated: mockIsAuthenticated,
  }),
  useCartStore: () => ({
    addItem: mockAddItem,
  }),
}));

// Mock dynamic import of ModelViewer
jest.mock("next/dynamic", () => () => {
  const DynamicComponent = () => <div data-testid="model-viewer">3D Viewer</div>;
  DynamicComponent.displayName = "ModelViewer";
  return DynamicComponent;
});

const mockTechnologies = [
  { id: "fdm", name: "FDM" },
  { id: "resin", name: "Resin" },
];

const mockMaterials: api.Material[] = [
  {
    id: 1,
    category_name: "PLA",
    name: "Standard",
    technology: "fdm",
    density: 1.24,
    colors: [
      { id: 1, name: "Black", hex_code: "#000000", is_active: true },
      { id: 2, name: "White", hex_code: "#FFFFFF", is_active: true },
    ],
  },
];

const mockProfiles: api.PrintProfile[] = [
  {
    id: 1,
    name: "Standard",
    technology: "fdm",
    layer_height_mm: 0.2,
    infill_percentage: 20,
    supports_enabled: false,
    quality_multiplier: 1.0,
    speed_multiplier: 1.0,
  },
];

describe("UploadQuoteForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsAuthenticated = false;

    (api.fetchTechnologies as jest.Mock).mockResolvedValue(mockTechnologies);
    (api.fetchMaterials as jest.Mock).mockResolvedValue(mockMaterials);
    (api.fetchProfiles as jest.Mock).mockResolvedValue(mockProfiles);
  });

  it("renders upload area", async () => {
    render(<UploadQuoteForm />);

    await waitFor(() => {
      expect(screen.getByText(/upload stl or 3mf file/i)).toBeInTheDocument();
    });
  });

  it("shows login prompt when not authenticated", async () => {
    mockIsAuthenticated = false;
    render(<UploadQuoteForm />);

    await waitFor(() => {
      expect(
        screen.getByText(/please log in to upload files and get quotes/i)
      ).toBeInTheDocument();
    });
  });

  it("loads technologies on mount", async () => {
    render(<UploadQuoteForm />);

    await waitFor(() => {
      expect(api.fetchTechnologies).toHaveBeenCalled();
    });
  });

  it("loads materials when technology changes", async () => {
    render(<UploadQuoteForm />);

    await waitFor(() => {
      expect(api.fetchMaterials).toHaveBeenCalledWith("fdm");
    });
  });

  it("shows error for invalid file type", async () => {
    mockIsAuthenticated = true;
    render(<UploadQuoteForm />);

    await waitFor(() => {
      expect(screen.getByText(/upload stl or 3mf file/i)).toBeInTheDocument();
    });

    const fileInput = screen.getByRole("textbox", { hidden: true }) ||
      document.querySelector('input[type="file"]');

    const invalidFile = new File(["content"], "test.txt", { type: "text/plain" });

    if (fileInput) {
      Object.defineProperty(fileInput, "files", {
        value: [invalidFile],
      });
      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
      });
    }
  });

  it("shows error for file too large", async () => {
    mockIsAuthenticated = true;
    render(<UploadQuoteForm />);

    await waitFor(() => {
      expect(screen.getByText(/upload stl or 3mf file/i)).toBeInTheDocument();
    });

    const fileInput = document.querySelector('input[type="file"]');

    // Create a mock file that reports being too large
    const largeFile = new File([""], "large.stl", { type: "application/sla" });
    Object.defineProperty(largeFile, "size", { value: 300 * 1024 * 1024 }); // 300MB

    if (fileInput) {
      Object.defineProperty(fileInput, "files", {
        value: [largeFile],
      });
      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/file too large/i)).toBeInTheDocument();
      });
    }
  });

  it("uploads file when valid and authenticated", async () => {
    mockIsAuthenticated = true;

    const mockModelFile = {
      id: 1,
      filename: "test.stl",
      metrics_status: "completed",
      volume_cm3: 10.5,
      surface_area_cm2: 25.0,
      bounding_box_mm: { x: 10, y: 10, z: 10 },
      is_watertight: true,
      is_manifold: true,
    };

    (api.uploadModel as jest.Mock).mockResolvedValue(mockModelFile);

    render(<UploadQuoteForm />);

    await waitFor(() => {
      expect(screen.getByText(/upload stl or 3mf file/i)).toBeInTheDocument();
    });

    const fileInput = document.querySelector('input[type="file"]');
    const validFile = new File(["solid cube"], "test.stl", {
      type: "application/sla",
    });

    if (fileInput) {
      Object.defineProperty(fileInput, "files", {
        value: [validFile],
      });
      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(api.uploadModel).toHaveBeenCalled();
      });
    }
  });

  it("disables get quote button when model not ready", async () => {
    mockIsAuthenticated = true;
    render(<UploadQuoteForm />);

    await waitFor(() => {
      const button = screen.getByRole("button", { name: /get instant quote/i });
      expect(button).toBeDisabled();
    });
  });

  it("renders material and profile selectors", async () => {
    render(<UploadQuoteForm />);

    await waitFor(() => {
      expect(screen.getByLabelText(/technology/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/material/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/color/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/print profile/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/quantity/i)).toBeInTheDocument();
    });
  });

  it("allows changing quantity", async () => {
    render(<UploadQuoteForm />);

    await waitFor(() => {
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: "5" } });
      expect(quantityInput).toHaveValue(5);
    });
  });

  it("enforces minimum quantity of 1", async () => {
    render(<UploadQuoteForm />);

    await waitFor(() => {
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: "0" } });
      expect(quantityInput).toHaveValue(1);
    });
  });
});
