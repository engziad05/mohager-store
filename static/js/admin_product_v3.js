document.addEventListener("DOMContentLoaded", function() {
    // Feature 1: Sync Product Color names to Product Image dropdowns
    function syncColorNamesToDropdowns() {
        let availableColors = [];
        
        const nameInputs = document.querySelectorAll('input[name$="-name_ar"]');
        
        nameInputs.forEach(nameInput => {
            const row = nameInput.closest('tr, .inline-related, .dynamic-form');
            if (row && (row.classList.contains('empty-form') || row.classList.contains('deleted') || row.style.display === 'none')) {
                return;
            }
            
            if (nameInput.value.trim() !== '') {
                const match = nameInput.name.match(/(.*)-name_ar$/);
                if (match) {
                    const prefix = match[1];
                    const idInput = document.querySelector(`input[name="${prefix}-id"]`);
                    
                    let colorId = idInput && idInput.value ? idInput.value : 'new_' + prefix;
                    let colorName = nameInput.value.trim();
                    availableColors.push({ id: colorId, name: colorName });
                }
            }
        });

        // 2. Update all ProductImage dropdowns
        const imageDropdowns = document.querySelectorAll('select[name$="-product_color"]');
        
        imageDropdowns.forEach(dropdown => {
            const currentValue = dropdown.value;
            const emptyOption = dropdown.querySelector('option[value=""]') || dropdown.options[0];
            
            let selectedText = "";
            if (currentValue && dropdown.options[dropdown.selectedIndex]) {
                selectedText = dropdown.options[dropdown.selectedIndex].text;
            }

            dropdown.innerHTML = '';
            if (emptyOption && emptyOption.value === "") {
                dropdown.appendChild(emptyOption);
            } else {
                dropdown.insertAdjacentHTML('beforeend', '<option value="">---------</option>');
            }

            availableColors.forEach(color => {
                const option = document.createElement('option');
                
                option.value = color.id; 
                option.text = color.name;
                if (color.id === currentValue || (selectedText && selectedText.endsWith(color.name))) {
                    option.selected = true;
                }
                dropdown.appendChild(option);
            });
        });
    }

    // Attach event listeners for typing in Color names
    document.body.addEventListener('input', function(e) {
        if (e.target.matches('input[name$="-name_ar"]')) {
            syncColorNamesToDropdowns();
        }
    });

    // Initial sync
    setTimeout(syncColorNamesToDropdowns, 500);

    // Also sync when a new inline is added
    document.body.addEventListener('click', function(e) {
        if (e.target.matches('.add-row a, .add-handler')) {
            setTimeout(syncColorNamesToDropdowns, 100);
        }
    });
});
