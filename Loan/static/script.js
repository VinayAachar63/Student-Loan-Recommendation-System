function qs(id){ return document.getElementById(id); }

// ... (toggleSection, onStudyTypeChange, onUnivLevelChange, computePercentage, displayCGPA, computeTotalAmount, submitForm, showRecommendations functions are unchanged) ...
function toggleSection(selectId, sections){
  const value = qs(selectId).value;
  for (const section in sections) {
    if (section === value) {
      qs(sections[section]).classList.remove('hidden');
    } else {
      qs(sections[section]).classList.add('hidden');
    }
  }
}
function onStudyTypeChange(){
  toggleSection('study_type', { college: 'college_section', university: 'university_section' });
  onUnivLevelChange(); // Reset inner university section
}
function onUnivLevelChange(){
  toggleSection('univ_level', { ug: 'ug_section', pg: 'pg_section' });
}
function computePercentage(totalId, obtainedId, displayId, label){
  const total = parseFloat(qs(totalId).value) || 0;
  const obt = parseFloat(qs(obtainedId).value) || 0;
  const display = qs(displayId);
  if(total > 0 && obt >= 0 && obt <= total){
    const perc = (obt / total) * 100;
    display.innerText = `${label} Percentage: ${perc.toFixed(2)}%`;
    display.style.color = 'green';
  } else {
    display.innerText = obt > total ? 'Obtained marks cannot exceed total marks.' : (total <= 0 ? '' : 'Please enter valid marks.');
    display.style.color = 'red';
  }
}
function displayCGPA(){
  const cgpa = parseFloat(qs('ug_cgpa').value);
  if(!isNaN(cgpa) && cgpa >= 0 && cgpa <= 10) {
    qs('ug_cgpa_display').innerText = `UG CGPA: ${cgpa.toFixed(2)} / 10`;
    qs('ug_cgpa_display').style.color = 'green';
  } else {
    qs('ug_cgpa_display').innerText = 'Please enter a valid CGPA between 0 and 10.';
    qs('ug_cgpa_display').style.color = 'red';
  }
}
function computeTotalAmount(){
  const years = parseInt(qs('loan_years').value) || 0;
  const fee = parseFloat(qs('college_fee').value) || 0;
  const total = years * fee;
  qs('total_amount_display').innerText = 'Total required amount: INR ' + total.toLocaleString();
  return total;
}
async function submitForm(){
  const requiredFields = ['student_name', 'email', 'phone', 'aadhaar', 'family_income', 'study_type'];
  for (const field of requiredFields) {
      if (!qs(field).value) {
          alert(`Please fill the required field: ${field.replace(/_/g, ' ')}`);
          return;
      }
  }
  const payload = {
    student_name: qs('student_name').value, email: qs('email').value, phone: qs('phone').value,
    aadhaar: qs('aadhaar').value, father_name: qs('father_name').value, father_phone: qs('father_phone').value,
    mother_name: qs('mother_name').value, mother_phone: qs('mother_phone').value,
    family_income: qs('family_income').value, study_type: qs('study_type').value,
    univ_level: qs('univ_level').value, t10_total: qs('t10_total').value, t10_obtained: qs('t10_obtained').value,
    t12_total: qs('t12_total').value, t12_obtained: qs('t12_obtained').value, ug_cgpa: qs('ug_cgpa').value,
    loan_years: qs('loan_years').value, college_fee: qs('college_fee').value
  };
  const loader = qs('form-loader');
  const button = loader.parentElement;
  loader.classList.remove('hidden');
  button.disabled = true;
  try{
    const resp = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if(!resp.ok){
      const err = await resp.json();
      // NEW: Handle authorization error
      if (resp.status === 401) {
        alert('Error: ' + (err.error || 'You must be logged in. Please log out and log back in.'));
      } else {
        throw new Error(err.error || resp.statusText);
      }
    } else {
        const data = await resp.json();
        showRecommendations(data);
    }
  } catch(e){
    alert('Error: ' + e.message);
  } finally {
    loader.classList.add('hidden');
    button.disabled = false;
  }
}
//
// Replace the functions 'showRecommendations' and 'applyForLoan' in your script.js
// The rest of the file is unchanged.
//

function showRecommendations(data){
  qs('results_section').classList.remove('hidden');
  const ul = qs('banks_list');
  const status = qs('rec_status');
  const total = data.total_amount || 0;
  const banks = data.recommended_banks || [];
  
  ul.innerHTML = '';
  status.innerHTML = `Found <strong>${banks.length}</strong> loan options for your requested amount of <strong>INR ${total.toLocaleString()}</strong>.`;

  if (banks.length === 0) {
    status.innerHTML += "<br>Unfortunately, no banks matched your profile. Please try adjusting the loan amount or other criteria.";
    qs('emi_calculator').classList.add('hidden');
    return;
  }
  
  banks.forEach(b => {
    const li = document.createElement('li');
    // We still need this to pass the bank data to the 'applyForLoan' (save) function
    const safeBank = JSON.stringify(b).replace(/'/g, "\\'");
    
    // (!!!) CHANGED (!!!) - Updated button layout
    li.innerHTML = `
      <div class="bank-details">
        <strong>${b.name}</strong>
        <span>${b.package} &bull; Interest: <strong>${b.interest_rate}%</strong></span>
      </div>
      <div class="bank-actions">
          <button class="btn btn-secondary" onclick="setupEMICalculator(${total}, ${b.interest_rate})">Calculate EMI</button>
          
          <button class="btn btn-secondary" onclick='applyForLoan(${safeBank}, this)'>
            <i class="fas fa-save"></i> Save Application
          </button>
          
          <a href="${b.url}" target="_blank" class="btn btn-apply">
            Apply at Bank <i class="fas fa-external-link-alt"></i>
          </a>
      </div>
    `;
    ul.appendChild(li);
  });
}


// --- MODIFIED: applyForLoan ---
// This function is now just for 'Saving' the application, not redirecting.
async function applyForLoan(bankDetails, buttonElement) {
    
    buttonElement.disabled = true;
    buttonElement.innerHTML = 'Saving...';
    
    const payload = {
        bank_name: bankDetails.name, 
        loan_package: bankDetails.package
    };
    
    try {
        const resp = await fetch('/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await resp.json();
        
        if (!resp.ok) { 
            throw new Error(result.error || 'Unknown server error.'); 
        }

        // (!!!) CHANGED (!!!) - This is the "Done" state.
        buttonElement.innerHTML = '<i class="fas fa-check"></i> Saved!';
        
    } catch (e) {
        alert('Application Failed: ' + e.message);
        buttonElement.disabled = false; // Re-enable if there was a failure
        buttonElement.innerHTML = '<i class="fas fa-save"></i> Save Application';
    }
}
// ... (setupEMICalculator, calculateEMI functions are unchanged) ...
function setupEMICalculator(amount, interest) {
    qs('emi_calculator').classList.remove('hidden');
    qs('emi_amount').value = amount;
    qs('emi_interest').value = interest;
    qs('emi_tenure').value = qs('loan_years').value;
    qs('emi_result').innerText = '';
    qs('emi_calculator').scrollIntoView({ behavior: 'smooth' });
}
function calculateEMI() {
    const P = parseFloat(qs('emi_amount').value);
    const annual_r = parseFloat(qs('emi_interest').value);
    const N = parseFloat(qs('emi_tenure').value);
    if (isNaN(P) || isNaN(annual_r) || isNaN(N) || P <= 0 || annual_r <= 0 || N <= 0) {
        qs('emi_result').innerText = 'Please enter valid numbers for all fields.';
        return;
    }
    const r = (annual_r / 12) / 100;
    const n = N * 12;
    const emi = P * r * (Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
    qs('emi_result').innerText = `Your estimated monthly payment is INR ${emi.toLocaleString('en-IN', { maximumFractionDigits: 0 })} for ${N} years.`;
}

// --- All Chatbot, Voice, and Speech Functions Removed ---


// MODIFIED: DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', () => {
  onStudyTypeChange();
  
  // --- Chatbot event listeners Removed ---
  
  // NOTE: The new 'checkSession()' function is now called from the
  // <script> block in index.html, so it's removed from here.
});