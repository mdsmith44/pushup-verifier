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

const uploadForm = document.getElementById("upload-form");
const videoFile = document.getElementById("video-file");
const cameraSide = document.getElementById("camera-side");
const uploadButton = document.getElementById("upload-button");
const uploadStatus = document.getElementById("upload-status");
const processingSpinner = document.getElementById("processing-spinner");
const processingHint = document.getElementById("processing-hint");

function setProcessingIndicator(active) {
  processingSpinner.hidden = !active;
  processingHint.hidden = !active;
}

let uploadApproved = false;
let uploading = false;

function updateUploadControls() {
  const disabled = !uploadApproved || uploading;
  videoFile.disabled = disabled;
  cameraSide.disabled = disabled;
  uploadButton.disabled = disabled;
}

function setUploadAccess(approved) {
  uploadApproved = approved;
  updateUploadControls();
}

function showUser(user) {
  setUploadAccess(false);
  const signedIn = Boolean(user && !user.expired);

  signIn.hidden = signedIn;
  signIn.disabled = false;
  signOut.hidden = !signedIn;
  signOut.disabled = false;

  status.textContent = signedIn
    ? `Signed in as ${user.profile.email || "a Google user"}.`
    : "Sign in with Google or your email address.";
}

signIn.addEventListener("click", async () => {
  signIn.disabled = true;
  status.textContent = "Opening Google sign-in…";

  try {
    await auth.signinRedirect();
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


async function checkApi(user) {
  if (!user || user.expired) return;

  status.textContent = "Signed in. Checking API connection…";

  try {
    const result = await fetch(
      "https://fe20wvd7l2.execute-api.us-east-2.amazonaws.com/me",
      {
        headers: {
          Authorization: `Bearer ${user.access_token}`,
        },
        cache: "no-store",
      },
    );

    if (!result.ok) {
      throw new Error(`API returned ${result.status}`);
    }

    const data = await result.json();

    if (data.user_id !== user.profile.sub) {
      throw new Error("API returned an unexpected user.");
    }

    setUploadAccess(data.can_process === true);

    uploadStatus.textContent = uploadApproved
        ? "Choose a video and camera side to upload."
        : "Uploads are limited to approved testers.";

    const permission = data.can_process
        ? "Video processing approved."
        : "Video processing is currently limited to approved testers.";

    status.textContent =
        `Signed in as ${user.profile.email || "a user"}. ${permission}`;
  } catch {
    status.textContent =
      "Signed in, but the API connection failed. Please try refreshing.";
  }
}

const jobResults = document.getElementById("job-results");
const resultVideo = document.getElementById("result-video");
const resultChart = document.getElementById("result-chart");
const resultVideoLink = document.getElementById("result-video-link");
const resultChartLink = document.getElementById("result-chart-link");
const resultReportLink = document.getElementById("result-report-link");

const apiUrl = "https://fe20wvd7l2.execute-api.us-east-2.amazonaws.com";

function latestJobKey(user) {
  return `pushup-latest-job:${user.profile.sub}`;
}

async function jobRequest(jobId, method = "GET", suffix = "") {
  const user = await auth.getUser();

  if (!user || user.expired) {
    setUploadAccess(false);
    throw new Error("Your session expired. Sign in again to view your job.");
  }

  const result = await fetch(
    `${apiUrl}/jobs/${encodeURIComponent(jobId)}${suffix}`,
    {
      method,
      headers: {
        Authorization: `Bearer ${user.access_token}`,
      },
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    },
  );

  const data = await result.json();

  if (!result.ok) {
    throw new Error(data.message || `Request failed (HTTP ${result.status}).`);
  }

  return data;
}

function displayResults(results) {
  resultVideo.src = results.video;
  resultChart.src = results.chart;
  resultVideoLink.href = results.video;
  resultChartLink.href = results.chart;
  resultReportLink.href = results.report;

  jobResults.hidden = false;
  uploadStatus.textContent =
    "Processing complete. Your results are below. Refresh to renew expired links.";
}

async function processAndWatch(jobId) {
  setProcessingIndicator(true);
  try {
  let job = await jobRequest(jobId);

  if (job.status === "ready") {
    uploadStatus.textContent = "Starting video processing…";
    await jobRequest(jobId, "POST", "/start");
  }

  const deadline = Date.now() + 20 * 60 * 1000;

  while (Date.now() < deadline) {
    job = await jobRequest(jobId);

    if (job.status === "completed") {
      displayResults(job.results);
      return;
    }

    if (job.status === "expired") {
      jobResults.hidden = true;
      resultVideo.pause();
      resultVideo.removeAttribute("src");
      resultVideo.load();
      resultChart.removeAttribute("src");

      const user = await auth.getUser();
      if (user) {
        const key = latestJobKey(user);
        if (sessionStorage.getItem(key) === jobId) {
          sessionStorage.removeItem(key);
        }
      }

      uploadStatus.textContent = job.message;
      return;
    }

    if (job.status === "failed") {
      throw new Error(job.message || "Video processing failed.");
    }

    if (job.status === "ready") {
      throw new Error(
        job.message || "Processing has not started. Refresh to try again.",
      );
    }

    if (job.status === "awaiting_upload") {
      throw new Error("This upload has not been verified.");
    }

    uploadStatus.textContent = job.status === "starting"
      ? "Preparing video processing…"
      : "Processing your video…";

    await new Promise((resolve) => setTimeout(resolve, 5000));
  }

  throw new Error(
    "Stopped checking after 20 minutes. Refresh to check your job again.",
  );
  } finally {
    setProcessingIndicator(false);
  }
}

async function resumeLatestJob(user) {
  const jobId = sessionStorage.getItem(latestJobKey(user));
  if (!jobId) return;

  uploading = true;
  updateUploadControls();

  try {
    await processAndWatch(jobId);
  } catch (error) {
    uploadStatus.textContent =
      `${error.message} Refresh to reconnect to your saved job.`;
  } finally {
    uploading = false;
    updateUploadControls();
  }
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!uploadApproved || uploading) return;

  const file = videoFile.files[0];
  if (!file) {
    uploadStatus.textContent = "Choose a video first.";
    return;
  }

  const extension = file.name.split(".").pop().toLowerCase();
  const contentTypes = {
    mp4: "video/mp4",
    mov: "video/quicktime",
    webm: "video/webm",
  };
  const contentType = contentTypes[extension];

  if (!contentType) {
    uploadStatus.textContent = "Choose an MP4, MOV, or WebM video.";
    return;
  }

  if (file.size === 0 || file.size > 200 * 1024 * 1024) {
    uploadStatus.textContent =
      "Choose a nonempty video no larger than 200 MiB.";
    return;
  }

  uploading = true;
  updateUploadControls();

  try {
    const user = await auth.getUser();

    if (!user || user.expired) {
      setUploadAccess(false);
      throw new Error("Your session expired. Sign out and sign in again.");
    }

    uploadStatus.textContent = "Preparing your upload…";

    const result = await fetch(
      "https://fe20wvd7l2.execute-api.us-east-2.amazonaws.com/jobs",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${user.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          size: file.size,
          content_type: contentType,
          side: cameraSide.value,
        }),
      },
    );

    if (!result.ok) {
      if (result.status === 401 || result.status === 403) {
        setUploadAccess(false);
      }
      throw new Error(`Could not prepare upload (HTTP ${result.status}).`);
    }

    const job = await result.json();
    const form = new FormData();

    for (const [name, value] of Object.entries(job.upload.fields)) {
      form.append(name, value);
    }

    // S3 requires the file field to come last.
    form.append("file", file);

    uploadStatus.textContent = "Uploading your video…";

    const uploaded = await fetch(job.upload.url, {
      method: "POST",
      body: form,
    });

    if (!uploaded.ok) {
      throw new Error(`Upload failed (HTTP ${uploaded.status}).`);
    }

    uploadStatus.textContent = "Verifying your upload…";

    const confirmation = await fetch(
      `https://fe20wvd7l2.execute-api.us-east-2.amazonaws.com/jobs/${job.job_id}/confirm`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${user.access_token}`,
        },
      },
    );

    if (!confirmation.ok) {
      throw new Error(
        `Video uploaded, but verification failed (HTTP ${confirmation.status}).`,
      );
    }

    sessionStorage.setItem(latestJobKey(user), job.job_id);
    videoFile.value = "";
    jobResults.hidden = true;

    await processAndWatch(job.job_id);
  } catch (error) {
    uploadStatus.textContent =
      error instanceof TypeError
        ? "Could not connect to the upload service. Please try again."
        : error.message;
  } finally {
    uploading = false;
    updateUploadControls();
  }
});

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
    const user = await auth.getUser();
    showUser(user);
    await checkApi(user);
    if (user && !user.expired && uploadApproved) {
      await resumeLatestJob(user);
    }
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
