document.addEventListener('DOMContentLoaded', function() {
    let currentPage = 1;

    function updatePagination(data) {
        const pagination = document.getElementById('pagination');
        pagination.innerHTML = '';

        if (data.has_previous) {
            pagination.insertAdjacentHTML('beforeend', `
                <li class="page-item">
                    <a class="page-link" href="#" aria-label="Previous" data-page="${currentPage - 1}">
                        <span aria-hidden="true">&laquo;</span>
                    </a>
                </li>
            `);
        }

        for (let i = 1; i <= data.total_pages; i++) {
            pagination.insertAdjacentHTML('beforeend', `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }

        if (data.has_next) {
            pagination.insertAdjacentHTML('beforeend', `
                <li class="page-item">
                    <a class="page-link" href="#" aria-label="Next" data-page="${currentPage + 1}">
                        <span aria-hidden="true">&raquo;</span>
                    </a>
                </li>
            `);
        }

        document.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                currentPage = parseInt(this.getAttribute('data-page'));
                loadProducts(currentPage);
            });
        });
    }

    function getSelectedValues(selector) {
        const selectedOptions = Array.from(document.querySelectorAll(selector))
            .filter(option => option.checked)
            .map(option => option.value);
        return selectedOptions.join(',');
    }

    


    document.getElementById('filters-form').addEventListener('submit', function(e) {
        e.preventDefault();
        currentPage = 1; // Go to the first page on filter submission
        loadProducts(currentPage);
    });

    document.getElementById('price_range').addEventListener('input', function() {
        document.getElementById('price_min_display').textContent = this.dataset.min;
        document.getElementById('price_max_display').textContent = this.value;
        document.getElementById('price_min').value = this.dataset.min;
        document.getElementById('price_max').value = this.value;
    });

});
