#!/bin/bash

# Dataset restructuring script
# This script renames directories and updates prompt.json paths

set -e  # Exit on any error

# Define base directory and paths
BASE_DIR="data/val"
ORIGINAL_TARGET_DIR="${BASE_DIR}/target-original"
NEW_TARGET_DIR="${BASE_DIR}/target"
SOURCE_PLAIN_DIR="${BASE_DIR}/source-plain"
NEW_SOURCE_PLAIN_DIR="${BASE_DIR}/plain-segmentation"
PROMPT_FILE="${BASE_DIR}/prompt.json"
BACKUP_PROMPT_FILE="${BASE_DIR}/prompt.json.backup"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if directory exists
check_directory() {
    if [ ! -d "$1" ]; then
        print_error "Directory $1 does not exist!"
        return 1
    fi
    return 0
}

# Function to check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        print_error "File $1 does not exist!"
        return 1
    fi
    return 0
}

# Function to create test cases
create_test_cases() {
    print_status "Creating test cases..."
    
    # Test case 1: Check original structure
    echo "=== Test Case 1: Original Structure ==="
    echo "Checking original directories..."
    ls -la "${BASE_DIR}/" | grep -E "(target-original|source-plain)"
    
    echo "Sample files in target-original:"
    ls "${ORIGINAL_TARGET_DIR}/" | head -3
    
    echo "Sample files in source-plain:"
    ls "${SOURCE_PLAIN_DIR}/" | head -3
    
    echo "Sample prompt.json entries:"
    head -3 "${PROMPT_FILE}"
    echo ""
}

# Function to perform the restructuring
perform_restructuring() {
    print_status "Starting restructuring process..."
    
    # Step 1: Rename target-original to target
    print_status "Step 1: Renaming target-original to target..."
    if check_directory "${ORIGINAL_TARGET_DIR}"; then
        if [ -d "${NEW_TARGET_DIR}" ]; then
            print_warning "Target directory ${NEW_TARGET_DIR} already exists. Removing it first..."
            rm -rf "${NEW_TARGET_DIR}"
        fi
        mv "${ORIGINAL_TARGET_DIR}" "${NEW_TARGET_DIR}"
        print_success "Renamed ${ORIGINAL_TARGET_DIR} to ${NEW_TARGET_DIR}"
    else
        return 1
    fi
    
    # Step 2: Rename source-plain to plain-segmentation
    print_status "Step 2: Renaming source-plain to plain-segmentation..."
    if check_directory "${SOURCE_PLAIN_DIR}"; then
        if [ -d "${NEW_SOURCE_PLAIN_DIR}" ]; then
            print_warning "Target directory ${NEW_SOURCE_PLAIN_DIR} already exists. Removing it first..."
            rm -rf "${NEW_SOURCE_PLAIN_DIR}"
        fi
        mv "${SOURCE_PLAIN_DIR}" "${NEW_SOURCE_PLAIN_DIR}"
        print_success "Renamed ${SOURCE_PLAIN_DIR} to ${NEW_SOURCE_PLAIN_DIR}"
    else
        return 1
    fi
    
    # Step 3: Update prompt.json
    print_status "Step 3: Updating prompt.json file..."
    if check_file "${PROMPT_FILE}"; then
        # Create backup
        cp "${PROMPT_FILE}" "${BACKUP_PROMPT_FILE}"
        print_status "Created backup: ${BACKUP_PROMPT_FILE}"
        
        # Update the paths in prompt.json
        sed -i 's|"target": "target-original/|"target": "target/|g' "${PROMPT_FILE}"
        
        print_success "Updated prompt.json file"
    else
        return 1
    fi
}

# Function to validate results
validate_results() {
    print_status "Validating results..."
    
    echo "=== Test Case 2: Post-Restructuring Validation ==="
    
    # Check new directory structure
    echo "New directory structure:"
    ls -la "${BASE_DIR}/" | grep -E "(target[^-]|plain-segmentation)"
    
    # Check if target directory exists and has files
    if [ -d "${NEW_TARGET_DIR}" ]; then
        file_count=$(ls "${NEW_TARGET_DIR}/" | wc -l)
        print_success "Target directory exists with ${file_count} files"
        echo "Sample files in target:"
        ls "${NEW_TARGET_DIR}/" | head -3
    else
        print_error "Target directory does not exist!"
        return 1
    fi
    
    # Check if plain-segmentation directory exists and has files
    if [ -d "${NEW_SOURCE_PLAIN_DIR}" ]; then
        file_count=$(ls "${NEW_SOURCE_PLAIN_DIR}/" | wc -l)
        print_success "Plain-segmentation directory exists with ${file_count} files"
        echo "Sample files in plain-segmentation:"
        ls "${NEW_SOURCE_PLAIN_DIR}/" | head -3
    else
        print_error "Plain-segmentation directory does not exist!"
        return 1
    fi
    
    # Check if old source-plain directory no longer exists
    if [ ! -d "${SOURCE_PLAIN_DIR}" ]; then
        print_success "Old source-plain directory successfully removed"
    else
        print_warning "Old source-plain directory still exists"
    fi
    
    # Validate prompt.json updates
    echo "Sample updated prompt.json entries:"
    head -3 "${PROMPT_FILE}"
    
    # Count occurrences of old and new paths
    old_target_count=$(grep -c "target-original/" "${PROMPT_FILE}" || true)
    new_target_count=$(grep -c '"target": "target/' "${PROMPT_FILE}" || true)
    
    echo "Path update validation:"
    echo "- Old 'target-original/' references: ${old_target_count}"
    echo "- New 'target/' references: ${new_target_count}"
    
    if [ "${old_target_count}" -eq 0 ] && [ "${new_target_count}" -gt 0 ]; then
        print_success "prompt.json paths updated successfully"
    else
        print_error "prompt.json path update may have failed"
        return 1
    fi
    
    echo ""
}

# Function to show before/after comparison
show_comparison() {
    print_status "Before/After Comparison:"
    
    echo "=== Test Case 3: File Integrity Check ==="
    
    # Compare file counts
    target_files=$(ls "${NEW_TARGET_DIR}/" | wc -l)
    plain_seg_files=$(ls "${NEW_SOURCE_PLAIN_DIR}/" | wc -l)
    
    echo "File counts:"
    echo "- Target directory: ${target_files} files"
    echo "- Plain-segmentation directory: ${plain_seg_files} files"
    
    # Check if a specific file exists in both locations (sample test)
    sample_file=$(ls "${NEW_TARGET_DIR}/" | head -1)
    if [ -n "${sample_file}" ]; then
        if [ -f "${NEW_TARGET_DIR}/${sample_file}" ]; then
            print_success "Sample file verification: ${sample_file} exists in target/"
        else
            print_error "Sample file verification failed"
        fi
    fi
    
    echo ""
}

# Main execution
main() {
    print_status "Starting dataset restructuring script..."
    echo "Working directory: $(pwd)"
    echo "Base directory: ${BASE_DIR}"
    echo ""
    
    # Pre-flight checks
    if ! check_directory "${BASE_DIR}"; then
        print_error "Base directory ${BASE_DIR} not found. Please run this script from the correct location."
        exit 1
    fi
    
    # Run test cases
    create_test_cases
    
    # Ask for confirmation
    echo -n "Do you want to proceed with the restructuring? (y/N): "
    read -r confirmation
    if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
        print_warning "Operation cancelled by user."
        exit 0
    fi
    
    # Perform restructuring
    if perform_restructuring; then
        print_success "Restructuring completed successfully!"
    else
        print_error "Restructuring failed!"
        exit 1
    fi
    
    # Validate results
    if validate_results; then
        print_success "Validation completed successfully!"
    else
        print_error "Validation failed!"
        exit 1
    fi
    
    # Show comparison
    show_comparison
    
    print_success "All operations completed successfully!"
    print_status "Backup of original prompt.json saved as: ${BACKUP_PROMPT_FILE}"
}

# Run main function
main "$@"