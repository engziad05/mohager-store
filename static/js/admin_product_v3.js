document.addEventListener("DOMContentLoaded", function() {
    // Feature 1: Sync Product Color names to Product Image dropdowns
    function syncColorNamesToDropdowns() {
        // 1. Get all current color names from the ProductColor inline
        const colorRows = document.querySelectorAll('#colors-group .dynamic-colors:not(.deleted), #productcolor_set-group .dynamic-productcolor_set:not(.deleted)');
        
        let availableColors = [];
        
        colorRows.forEach(row => {
            if (row.classList.contains('empty-form')) return;
            const nameInput = row.querySelector('input[name$="-name_ar"]');
            
            if (nameInput && nameInput.value.trim() !== '') {
                let prefix = row.id;
                if (!prefix) {
                    const match = nameInput.name.match(/(.*)-name_ar$/);
                    if (match) prefix = match[1];
                }
                const idInput = document.querySelector(`input[name="${prefix}-id"]`);
                
                let colorId = idInput && idInput.value ? idInput.value : 'new_' + prefix;
                let colorName = nameInput.value.trim();
                availableColors.push({ id: colorId, name: colorName });
            }
        });

        // 2. Update all ProductImage dropdowns
        const imageDropdowns = document.querySelectorAll('#images-group select[name$="-product_color"], #productimage_set-group select[name$="-product_color"]');
        
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
        if (e.target.matches('#colors-group input[name$="-name_ar"], #productcolor_set-group input[name$="-name_ar"]')) {
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
