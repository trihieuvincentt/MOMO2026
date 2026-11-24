const resultBox = document.querySelector('#result');
const messageForm = document.querySelector('#message-form');
const urlForm = document.querySelector('#url-form');
const ocrForm = document.querySelector('#ocr-form');
const ocrText = document.querySelector('#ocr-text');
const ocrConfirm = document.querySelector('#ocr-confirm');
const ocrMeta = document.querySelector('#ocr-meta');

function showError(message) {
  resultBox.innerHTML = `<div class="result-body"><div class="result-section"><h4>Request error</h4><p>${escapeHtml(message)}</p></div></div>`;
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
}
function setLoading(label) { resultBox.innerHTML = `<div class="empty-result"><span>◌</span><p>${escapeHtml(label)}</p></div>`; }
function renderResult(data, title) {
  const findings = Array.isArray(data.findings) ? data.findings : [];
  const limitations = Array.isArray(data.limitations) ? data.limitations : [];
  const risk = data.risk_assessment || data.risk;
  const recs = risk && Array.isArray(risk.recommendations) ? risk.recommendations : [];
  const artifacts = Array.isArray(data.artifacts) ? data.artifacts : [];
  const campaignMatches = Array.isArray(data.campaign_matches) ? data.campaign_matches : [];
  const findingHtml = findings.map((item) => {
    const finding = item.finding || item;
    return `<div class="finding"><strong>${escapeHtml(finding.category || 'Indicator')} · ${escapeHtml(finding.severity || 'unknown')}</strong><small>${escapeHtml(finding.description || '')}</small></div>`;
  }).join('') || '<p>No known signal found. Absence of a finding is not a safety guarantee.</p>';
  const recHtml = recs.map((item) => `<li>${escapeHtml(item.action || '')}</li>`).join('');
  const artifactHtml = artifacts.map((item) => `<li><strong>${escapeHtml(item.type || 'artifact')}</strong>: ${escapeHtml(item.display_value || item.normalized_value || '')}</li>`).join('') || '<li>No reusable artifacts extracted.</li>';
  const campaignHtml = campaignMatches.map((match) => `<div class="finding"><strong>Related case match · score ${escapeHtml(match.score)}</strong><small>Shared: ${escapeHtml((match.shared_artifact_values || []).join(', '))}</small></div>`).join('') || '<p>No prior campaign match found. This does not mean the message is safe.</p>';
  const limitHtml = limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('');
  resultBox.innerHTML = `<div class="result-header"><strong>${escapeHtml(title)}</strong><span class="risk-badge">${escapeHtml((risk && risk.category) || data.status || 'complete')}</span></div><div class="result-body"><div class="result-section"><h4>Summary</h4><p>${escapeHtml(data.summary || (risk && risk.explanation) || 'Analysis complete.')}</p></div><div class="result-section"><h4>Findings</h4>${findingHtml}</div><div class="result-section"><h4>Extracted artifacts</h4><ul>${artifactHtml}</ul></div><div class="result-section"><h4>Campaign intelligence</h4>${campaignHtml}</div>${recHtml ? `<div class="result-section"><h4>Recommended next steps</h4><ul>${recHtml}</ul></div>` : ''}${limitHtml ? `<div class="result-section"><h4>Limitations</h4><ul>${limitHtml}</ul></div>` : ''}</div>`;
}
async function requestJson(path, options) {
  const response = await fetch(path, options);
  let data;
  try { data = await response.json(); } catch { throw new Error('The service returned an unreadable response.'); }
  if (!response.ok) throw new Error(data.detail || 'The request could not be completed.');
  return data;
}
async function scanMessage(text) {
  if (!text.trim()) return showError('Enter or confirm message text before scanning.');
  setLoading('Analyzing message…');
  try { renderResult(await requestJson('/api/v1/message/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})}), 'Message analysis'); }
  catch (error) { showError(error.message); }
}
async function scanUrl(url) {
  if (!url.trim()) return showError('Enter a URL before scanning.');
  setLoading('Checking reputation sources…');
  try { renderResult(await requestJson('/api/v1/url/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url})}), 'URL reputation'); }
  catch (error) { showError(error.message); }
}
async function extractOcr(file) {
  const form = new FormData(); form.append('image', file); form.append('language_hint', 'en');
  ocrText.disabled = true; ocrConfirm.disabled = true; ocrMeta.hidden = true; setLoading('Extracting text…');
  try {
    const data = await requestJson('/api/v1/ocr/extract', {method:'POST', body:form});
    ocrText.value = data.extracted_text || ''; ocrText.disabled = false; ocrConfirm.disabled = !ocrText.value.trim();
    ocrMeta.textContent = `${data.ocr_source || 'unknown'}${data.provider_notice ? ` · ${data.provider_notice}` : ''}${data.warnings?.length ? ` · ${data.warnings.join(' ')}` : ''}`;
    ocrMeta.hidden = false; resultBox.innerHTML = '<div class="empty-result"><span>✓</span><p>Review the extracted text above.</p><small>Nothing has been sent to Message Scanner yet.</small></div>';
  } catch (error) { ocrText.value = ''; showError(error.message); }
}
messageForm.addEventListener('submit', (event) => { event.preventDefault(); scanMessage(document.querySelector('#message-input').value); });
urlForm.addEventListener('submit', (event) => { event.preventDefault(); scanUrl(document.querySelector('#url-input').value); });
ocrForm.addEventListener('submit', (event) => event.preventDefault());
document.querySelector('#image-input').addEventListener('change', (event) => { if (event.target.files[0]) extractOcr(event.target.files[0]); });
ocrConfirm.addEventListener('click', () => scanMessage(ocrText.value));
document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
  document.querySelectorAll('.tool-panel').forEach((panel) => { const active = panel.dataset.panel === tab.dataset.tab; panel.hidden = !active; panel.classList.toggle('active', active); });
}));
