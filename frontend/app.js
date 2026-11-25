const resultBox = document.querySelector('#result');
const messageForm = document.querySelector('#message-form');
const urlForm = document.querySelector('#url-form');
const ocrForm = document.querySelector('#ocr-form');
const ocrText = document.querySelector('#ocr-text');
const ocrConfirm = document.querySelector('#ocr-confirm');
const ocrMeta = document.querySelector('#ocr-meta');
const websiteForm = document.querySelector('#website-form');
const websiteInput = document.querySelector('#website-input');
const brandInput = document.querySelector('#brand-input');
const forceWebsite = document.querySelector('#website-force');

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
function renderWebsiteResult(data) {
  const fusion = data.fusion || {};
  const snapshot = data.snapshot || {};
  const content = data.content || {};
  const links = Array.isArray(data.links?.links) ? data.links.links : [];
  const visual = data.visual || {};
  const reasons = Array.isArray(fusion.reasons) ? fusion.reasons : [];
  const reasonHtml = reasons.map((reason) => `<div class="finding"><strong>${escapeHtml(reason.evidence_source)} · ${escapeHtml(reason.severity)}</strong><small>${escapeHtml(reason.description)} (+${escapeHtml(reason.score)})</small></div>`).join('') || '<p>No corroborated risk reason was found.</p>';
  const linkHtml = links.map((link) => `<li><strong>${escapeHtml(link.role || 'link')}</strong>: ${escapeHtml(link.domain || link.url)} · ${escapeHtml(link.relationship || '')}${link.indicators?.length ? ` · ${escapeHtml(link.indicators.join(', '))}` : ''}</li>`).join('') || '<li>No extracted links.</li>';
  const formHtml = Array.isArray(content.forms) ? content.forms.map((form) => `<li>${escapeHtml(form.method || 'get')} ${escapeHtml(form.action_url || '')}: ${escapeHtml((form.fields || []).map((field) => field.name).join(', '))}</li>`).join('') : '';
  const visualSignals = Array.isArray(visual.indicators) ? visual.indicators.map((item) => `<div class="finding"><strong>${escapeHtml(item.category || 'visual indicator')} · ${Math.round(Number(item.confidence || 0) * 100)}%</strong><small>${escapeHtml(item.description || '')}</small></div>`).join('') : '';
  const visualForms = Array.isArray(visual.forms) ? visual.forms.map((form) => `<li>${escapeHtml(form.purpose || 'form')}: ${escapeHtml((form.fields || []).join(', '))}</li>`).join('') : '';
  const visualSensitive = Array.isArray(visual.sensitive_data_requested) && visual.sensitive_data_requested.length ? `<p>Sensitive fields visually identified: ${escapeHtml(visual.sensitive_data_requested.join(', '))}</p>` : '';
  const visualHtml = visual.status === 'success' ? `<p>Detected brands: ${escapeHtml((visual.detected_brands || []).join(', ') || 'none')} · Site type: ${escapeHtml(visual.site_type || 'unknown')}</p>${visualForms ? `<ul>${visualForms}</ul>` : ''}${visualSensitive}${visualSignals || '<p>No visual indicators returned.</p>'}` : `<p>Visual analysis ${escapeHtml(visual.status || 'unavailable')}. ${escapeHtml((visual.limitations || []).join(' '))}</p>`;
  resultBox.innerHTML = `<div class="result-header"><strong>Website investigation ${data.cache_hit ? '· cached' : ''}</strong><span class="risk-badge">${escapeHtml(fusion.category || 'unknown')} · ${escapeHtml(fusion.score ?? 0)}/100</span></div><div class="result-body"><div class="result-section"><h4>Snapshot</h4><p>${escapeHtml(snapshot.title || 'Untitled')} · ${escapeHtml(snapshot.final_url || '')}</p></div><div class="result-section"><h4>Why this result</h4>${reasonHtml}</div><div class="result-section"><h4>Visual analysis</h4>${visualHtml || '<p>Visual analysis unavailable.</p>'}</div><div class="result-section"><h4>Forms and sensitive fields</h4><ul>${formHtml || '<li>No forms extracted.</li>'}</ul></div><div class="result-section"><h4>Links and domains</h4><ul>${linkHtml}</ul></div>${fusion.limitations?.length ? `<div class="result-section"><h4>Limitations</h4><ul>${fusion.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div>` : ''}</div>`;
}
async function investigateWebsite(url, brands) {
  if (!url.trim()) return showError('Enter a website URL before investigating.');
  setLoading('Capturing page, extracting evidence, and fusing risk…');
  try {
    const data = await requestJson('/api/v1/websites/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url, claimed_brands: brands.split(',').map((item) => item.trim()).filter(Boolean), force_reanalysis: forceWebsite.checked})});
    renderWebsiteResult(data);
  } catch (error) { showError(error.message); }
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
websiteForm.addEventListener('submit', (event) => { event.preventDefault(); investigateWebsite(websiteInput.value, brandInput.value); });
ocrForm.addEventListener('submit', (event) => event.preventDefault());
document.querySelector('#image-input').addEventListener('change', (event) => { if (event.target.files[0]) extractOcr(event.target.files[0]); });
ocrConfirm.addEventListener('click', () => scanMessage(ocrText.value));
document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
  document.querySelectorAll('.tool-panel').forEach((panel) => { const active = panel.dataset.panel === tab.dataset.tab; panel.hidden = !active; panel.classList.toggle('active', active); });
}));
