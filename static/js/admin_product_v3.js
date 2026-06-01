document.addEventListener("DOMContentLoaded", function() {
    // Feature 1: Sync Product Print names to Product Image dropdowns
    function syncPrintNamesToDropdowns() {
        // 1. Get all current print names from the ProductPrint inline
        const printRows = document.querySelectorAll('#prints-group .dynamic-prints:not(.deleted), #productprint_set-group .dynamic-productprint_set:not(.deleted)');
        
        let availablePrints = [];
        // Assuming there might be an empty template row which we should ignore
        
        printRows.forEach(row => {
            if (row.classList.contains('empty-form')) return;
            const nameInput = row.querySelector('input[name$="-name"]');
            
            if (nameInput && nameInput.value.trim() !== '') {
                // More robust way to find the ID input (it might be outside the row wrapper in some admin themes)
                let prefix = row.id;
                if (!prefix) {
                    const match = nameInput.name.match(/(.*)-name$/);
                    if (match) prefix = match[1];
                }
                const idInput = document.querySelector(`input[name="${prefix}-id"]`);
                
                // Determine ID if exists, otherwise generate a temporary one based on index
                let printId = idInput && idInput.value ? idInput.value : 'new_' + prefix;
                let printName = nameInput.value.trim();
                availablePrints.push({ id: printId, name: printName });
            }
        });

        // 2. Update all ProductImage dropdowns
        const imageDropdowns = document.querySelectorAll('#images-group select[name$="-product_print"], #productimage_set-group select[name$="-product_print"]');
        
        imageDropdowns.forEach(dropdown => {
            const currentValue = dropdown.value;
            // Keep the empty/default option
            const emptyOption = dropdown.querySelector('option[value=""]') || dropdown.options[0];
            
            // Store currently selected text in case it's a new unsaved one
            let selectedText = "";
            if (currentValue && dropdown.options[dropdown.selectedIndex]) {
                selectedText = dropdown.options[dropdown.selectedIndex].text;
            }

            // Clear options except the first empty one
            dropdown.innerHTML = '';
            if (emptyOption && emptyOption.value === "") {
                dropdown.appendChild(emptyOption);
            } else {
                dropdown.insertAdjacentHTML('beforeend', '<option value="">---------</option>');
            }

            // Append updated options
            availablePrints.forEach(print => {
                const option = document.createElement('option');
                // Use the stringified name as value for new items?
                // The issue is backend won't accept a string if it expects an ID.
                // Actually, if it's a new print, it doesn't have an ID yet.
                // We CANNOT save a ProductImage linked to an unsaved ProductPrint in the same request, because ProductImage.product_print expects a valid FK id.
                // Wait, Django Admin saves inlines in order?
                // No, Django forms validate first. If ProductImage form receives an invalid FK (like 'new_print'), it will throw a validation error.
                // Django admin doesn't support creating an inline item that is dependent on another new inline item in the same submit, UNLESS they are saved in a specific order and the FK is handled.
                // Because of this, it's actually not natively possible in Django to link two new inlines together before saving!
                
                option.value = print.id; 
                // We might only be able to populate existing ones, or we can just populate the text for UX, but they will fail validation if they select a 'new_' id.
                // Let's check how Unfold handles it. If it's a standard Django admin formset, selecting a non-existent ID will raise "Select a valid choice. That choice is not one of the available choices."
                
                // Let's still add them, but if it's a "new_" ID, maybe we just use the name for visual feedback, but they must save.
                // Or better, we only allow this for visual?
                // The user says: "اسم الطبعه بيظهر لما اعمل سيف الاول" (print name appears after I save first).
                // They understand they need to save, but they just want it to appear? No, they probably want to be able to select it without saving first!
                // But Django doesn't allow saving a ForeignKey to an object that hasn't been created yet in the same formset submission easily (it requires custom formset `save` method overriding to map temporary IDs).
                // If they just want to avoid the page reload, maybe we can just tell them they still have to save first, OR we implement the visual part but let them know.
                // Actually, if we use the string text, can we override the `ProductImageInline` form to accept the name and link it in `save_model`?
                // Yes! If we send the name, we can override `ProductImageInline.form.clean` to ignore the invalid choice, and in `ModelAdmin.save_related`, we can link them.
                // But that's very complex. Let's start by just updating the options. If they select a new one, it will fail validation, alerting them to save first.
                // Or maybe they just want the UX to be smoother.
                
                option.text = print.name;
                if (print.id === currentValue || (selectedText && selectedText.endsWith(print.name))) {
                    option.selected = true;
                }
                dropdown.appendChild(option);
            });
        });
    }

    // Attach event listeners for typing in Print names
    document.body.addEventListener('input', function(e) {
        if (e.target.matches('#prints-group input[name$="-name"], #productprint_set-group input[name$="-name"]')) {
            syncPrintNamesToDropdowns();
        }
    });

    // We allow the user to select new prints. 
    // The backend now handles saving the new print and linking the image to it automatically.
    // Initial sync
    setTimeout(syncPrintNamesToDropdowns, 500);

    // Also sync when a new inline is added
    document.body.addEventListener('click', function(e) {
        if (e.target.matches('.add-row a, .add-handler')) {
            setTimeout(syncPrintNamesToDropdowns, 100);
        }
    });
});
