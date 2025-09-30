// Main JavaScript file for To-Do List App

$(document).ready(function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form validation demo for email/password fields
    // This is just a demo as per requirements, not actually used in the app
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function validatePassword(password) {
        // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
        const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/;
        return re.test(password);
    }

    // Example validation function for demo purposes
    $('#demoEmailInput').on('input', function() {
        const email = $(this).val();
        if (!validateEmail(email) && email !== '') {
            $(this).addClass('is-invalid');
        } else {
            $(this).removeClass('is-invalid');
        }
    });

    $('#demoPasswordInput').on('input', function() {
        const password = $(this).val();
        if (!validatePassword(password) && password !== '') {
            $(this).addClass('is-invalid');
        } else {
            $(this).removeClass('is-invalid');
        }
    });

    // Task form validation
    $('#taskForm').on('submit', function(e) {
        let isValid = true;
        
        // Reset validation states
        $('.is-invalid').removeClass('is-invalid');
        
        // Validate title (required)
        const title = $('#title').val().trim();
        if (title === '') {
            $('#title').addClass('is-invalid');
            isValid = false;
        }
        
        // Validate due date format if provided
        const dueDate = $('#due_date').val();
        if (dueDate && !isValidDate(dueDate)) {
            $('#due_date').addClass('is-invalid');
            isValid = false;
        }
        
        if (!isValid) {
            e.preventDefault();
        } else {
            // Disable submit button to prevent double submission
            $('#submitBtn').prop('disabled', true).html(
                '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...');
        }
    });
    
    // Helper function to validate date format
    function isValidDate(dateString) {
        const regex = /^\d{4}-\d{2}-\d{2}$/;
        if (!regex.test(dateString)) return false;
        
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    }
    
    // Confirmation before delete
    $('.delete-btn').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this task?')) {
            e.preventDefault();
        }
    });
    
    // Task card hover effects
    $('.task-item').hover(
        function() {
            $(this).find('.card').addClass('shadow');
        },
        function() {
            $(this).find('.card').removeClass('shadow');
        }
    );
    
    // Fade in tasks for a nice effect
    $('.task-item').each(function(index) {
        $(this).delay(index * 100).fadeIn(500);
    });
});