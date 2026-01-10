import { renderHook, act } from "@testing-library/react";

// We need to test the store without persistence for testing
jest.mock("zustand/middleware", () => ({
  persist: (fn: any) => fn,
}));

// Clear localStorage before each test
beforeEach(() => {
  localStorage.clear();
});

describe("useAuthStore", () => {
  // Re-import after mock is set up
  let useAuthStore: any;

  beforeEach(async () => {
    jest.resetModules();
    const store = await import("../../lib/store");
    useAuthStore = store.useAuthStore;
  });

  it("starts with no authentication", () => {
    const { result } = renderHook(() => useAuthStore());

    expect(result.current.token).toBeNull();
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("sets authentication state", () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      id: 1,
      email: "test@example.com",
      name: "Test User",
      role: "customer",
    };

    act(() => {
      result.current.setAuth("test-token", mockUser);
    });

    expect(result.current.token).toBe("test-token");
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("clears authentication state on logout", () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      id: 1,
      email: "test@example.com",
      name: "Test User",
      role: "customer",
    };

    act(() => {
      result.current.setAuth("test-token", mockUser);
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.token).toBeNull();
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});

describe("useCartStore", () => {
  let useCartStore: any;

  beforeEach(async () => {
    jest.resetModules();
    const store = await import("../../lib/store");
    useCartStore = store.useCartStore;
  });

  it("starts with empty cart", () => {
    const { result } = renderHook(() => useCartStore());

    expect(result.current.items).toEqual([]);
    expect(result.current.totalItems).toBe(0);
    expect(result.current.totalPrice).toBe(0);
  });

  it("adds items to cart", () => {
    const { result } = renderHook(() => useCartStore());

    const mockQuote = {
      id: 1,
      model_file_id: 1,
      material_id: 1,
      color_id: 1,
      profile_id: 1,
      quantity: 2,
      total_price: 25.0,
      unit_price: 12.5,
      lead_time_days: 3,
      breakdown: {
        material_cost: 5.0,
        machine_cost: 10.0,
        handling_fee: 4.0,
        support_cost: 0,
      },
    };

    act(() => {
      result.current.addItem(mockQuote);
    });

    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].quote).toEqual(mockQuote);
    expect(result.current.totalItems).toBe(2);
    expect(result.current.totalPrice).toBe(25.0);
  });

  it("removes items from cart", () => {
    const { result } = renderHook(() => useCartStore());

    const mockQuote = {
      id: 1,
      model_file_id: 1,
      material_id: 1,
      color_id: 1,
      profile_id: 1,
      quantity: 1,
      total_price: 15.0,
      unit_price: 15.0,
      lead_time_days: 3,
      breakdown: {
        material_cost: 5.0,
        machine_cost: 6.0,
        handling_fee: 4.0,
        support_cost: 0,
      },
    };

    act(() => {
      result.current.addItem(mockQuote);
    });

    const itemId = result.current.items[0].id;

    act(() => {
      result.current.removeItem(itemId);
    });

    expect(result.current.items).toHaveLength(0);
    expect(result.current.totalItems).toBe(0);
    expect(result.current.totalPrice).toBe(0);
  });

  it("clears cart", () => {
    const { result } = renderHook(() => useCartStore());

    const mockQuote1 = {
      id: 1,
      model_file_id: 1,
      material_id: 1,
      color_id: 1,
      profile_id: 1,
      quantity: 1,
      total_price: 15.0,
      unit_price: 15.0,
      lead_time_days: 3,
      breakdown: {
        material_cost: 5.0,
        machine_cost: 6.0,
        handling_fee: 4.0,
        support_cost: 0,
      },
    };

    const mockQuote2 = {
      id: 2,
      model_file_id: 2,
      material_id: 1,
      color_id: 1,
      profile_id: 1,
      quantity: 2,
      total_price: 30.0,
      unit_price: 15.0,
      lead_time_days: 3,
      breakdown: {
        material_cost: 10.0,
        machine_cost: 12.0,
        handling_fee: 4.0,
        support_cost: 4.0,
      },
    };

    act(() => {
      result.current.addItem(mockQuote1);
      result.current.addItem(mockQuote2);
    });

    expect(result.current.items).toHaveLength(2);

    act(() => {
      result.current.clearCart();
    });

    expect(result.current.items).toHaveLength(0);
    expect(result.current.totalItems).toBe(0);
    expect(result.current.totalPrice).toBe(0);
  });

  it("calculates totals correctly with multiple items", () => {
    const { result } = renderHook(() => useCartStore());

    const quote1 = {
      id: 1,
      model_file_id: 1,
      material_id: 1,
      color_id: 1,
      profile_id: 1,
      quantity: 2,
      total_price: 20.0,
      unit_price: 10.0,
      lead_time_days: 3,
      breakdown: {
        material_cost: 5.0,
        machine_cost: 6.0,
        handling_fee: 4.0,
        support_cost: 0,
      },
    };

    const quote2 = {
      id: 2,
      model_file_id: 2,
      material_id: 2,
      color_id: 2,
      profile_id: 1,
      quantity: 3,
      total_price: 45.0,
      unit_price: 15.0,
      lead_time_days: 5,
      breakdown: {
        material_cost: 10.0,
        machine_cost: 15.0,
        handling_fee: 4.0,
        support_cost: 6.0,
      },
    };

    act(() => {
      result.current.addItem(quote1);
      result.current.addItem(quote2);
    });

    expect(result.current.totalItems).toBe(5); // 2 + 3
    expect(result.current.totalPrice).toBe(65.0); // 20 + 45
  });
});
