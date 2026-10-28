import { GitHubProvider } from "./github.js";
import { OFFICIAL_REPO } from "../constants.js";

export class ArcanaProvider extends GitHubProvider {
  constructor() {
    super(OFFICIAL_REPO.owner, OFFICIAL_REPO.name, {
      name: "arcana",
      displayName: "Arcana (official)",
      branch: OFFICIAL_REPO.branch,
    });
  }
}
