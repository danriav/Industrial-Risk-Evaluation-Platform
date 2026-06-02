import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { App } from "./main";

describe("MERO frontend smoke", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  it("renders the operational dashboard without persisting Basic credentials", async () => {
    const user = userEvent.setup();

    render(<App />);

    expect(screen.getByRole("heading", { name: "Riesgo operacional" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Bitacora" })).toBeInTheDocument();
    expect(screen.getByText("Autenticacion requerida")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Usuario Basic"), "mero_admin");
    await user.type(screen.getByLabelText("Password Basic"), "secret-value");

    expect(screen.getByText("Actualizacion requerida")).toBeInTheDocument();
    expect(window.sessionStorage.getItem("mero.basic.credentials")).toBeNull();
    expect(window.sessionStorage.length).toBe(0);
    expect(window.localStorage.length).toBe(0);
  });
});
