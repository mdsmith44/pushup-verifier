import { UserManager, WebStorageStateStore } from "oidc-client-ts";

const siteUrl = "https://dg05a9no1enlg.cloudfront.net/";
const cognitoDomain =
  "https://us-east-2ked1hcukt.auth.us-east-2.amazoncognito.com";
const clientId = "1fo6v4t111g1urebnkenv648hp";

const auth = new UserManager({
  authority:
    "https://cognito-idp.us-east-2.amazonaws.com/us-east-2_kED1hCUkT",
  client_id: clientId,
  redirect_uri: siteUrl,
  response_type: "code",
  scope: "openid email profile",
  automaticSilentRenew: false,
  loadUserInfo: false,
  userStore: new WebStorageStateStore({
    store: window.sessionStorage,
  }),
  stateStore: new WebStorageStateStore({
    store: window.sessionStorage,
  }),
});

const status = document.getElementById("auth-status");
const signIn = document.getElementById("sign-in");
const signOut = document.getElementById("sign-out");

function showUser(user) {
  const signedIn = Boolean(user && !user.expired);

  signIn.hidden = signedIn;
  signIn.disabled = false;
  signOut.hidden = !signedIn;
  signOut.disabled = false;

  status.textContent = signedIn
    ? `Signed in as ${user.profile.email || "a Google user"}.`
    : "Sign in with Google to use your account.";
}

signIn.addEventListener("click", async () => {
  signIn.disabled = true;
  status.textContent = "Opening Google sign-in…";

  try {
    await auth.signinRedirect({
      extraQueryParams: { identity_provider: "Google" },
    });
  } catch {
    status.textContent = "Could not start sign-in. Please try again.";
    signIn.disabled = false;
  }
});

signOut.addEventListener("click", async () => {
  signOut.disabled = true;

  try {
    await auth.removeUser();

    const logoutUrl = new URL("/logout", cognitoDomain);
    logoutUrl.searchParams.set("client_id", clientId);
    logoutUrl.searchParams.set("logout_uri", siteUrl);

    window.location.assign(logoutUrl.href);
  } catch {
    status.textContent = "Could not sign out. Please try again.";
    signOut.disabled = false;
  }
});

auth.events.addAccessTokenExpired(() => showUser(null));

async function initialize() {
  const parameters = new URLSearchParams(window.location.search);
  const isCallback =
    parameters.has("code") || parameters.has("error");

  try {
    if (isCallback) {
      status.textContent = "Completing sign-in…";
      await auth.signinRedirectCallback();
    }

    await auth.clearStaleState();
    showUser(await auth.getUser());
  } catch {
    await auth.removeUser();
    showUser(null);
    status.textContent =
      "Sign-in could not be completed. Please try signing in again.";
  } finally {
    if (isCallback) {
      // Remove the temporary authentication details from the address bar.
      const cleanUrl = new URL(window.location.href);
      for (const key of [
        "code", "state", "error", "error_description", "error_uri",
      ]) {
        cleanUrl.searchParams.delete(key);
      }
      window.history.replaceState({}, "", cleanUrl.href);
    }
  }
}

initialize();