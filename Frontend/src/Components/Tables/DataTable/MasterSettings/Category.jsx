import React, { Fragment, useState, useEffect } from 'react';
import {
    Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Button, Modal, ModalHeader, ModalBody, Input, FormGroup, Label, FormFeedback,
    Badge
} from 'reactstrap';
import { FaTrashAlt, FaArrowUp, FaArrowDown, FaPencilAlt } from 'react-icons/fa';
import Swal from 'sweetalert2';
import { getCategories, addCategory, updateCategory, deleteCategory } from '../../../../Services/Authentication';
import './Settings.css';

const Category = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [categories, setCategories] = useState([]);
    const [totalPages, setTotalPages] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [editing, setEditing] = useState(false);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [modalOpen, setModalOpen] = useState(false);
    const [newCategory, setNewCategory] = useState({ name: '', status: 'Active', });
    const [editIndex, setEditIndex] = useState(null);
    const [errors, setErrors] = useState({});
    // const [loading, setLoading] = useState(true);
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);
    const [error, setError] = useState(null);

    // Fetch categories from API
    useEffect(() => {
        fetchedCategories(searchQuery);

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage, searchQuery]);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchedCategories = async (query = '') => {
        try {
            const data = await getCategories(currentPage, itemsPerPage, query);
            const sortedCategories = data.results.sort((a, b) => b.id - a.id);
            setCategories(sortedCategories);
            setTotalPages(Math.ceil(data.count / itemsPerPage));
        } catch (err) {
            setError(err.message);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            setCurrentPage(1); // Reset to page 1 on new search
            fetchedCategories(searchQuery);
        }
    };

    const handleSearchClick = () => {
        setCurrentPage(1);
        fetchedCategories(searchQuery);
    };

    const updateLocalStorage = (updatedCategories) => {
        localStorage.setItem('categories', JSON.stringify(updatedCategories));
    };

    const toggleModal = (clearForm = true) => {
        setModalOpen(!modalOpen);
        if (clearForm) resetForm();
    };

    const handleAddOrEditCategory = async (event) => {
        event.preventDefault();
        if (!validateForm()) return;

        try {
            if (editing) {
                const updatedCategory = {
                    ...newCategory,
                    status: newCategory.status === 'Active' || newCategory.status === true,
                };
                console.log('Updating category:', updatedCategory);
                await updateCategory(updatedCategory, updatedCategory.id);
                const updatedCategories = categories.map((category, index) =>
                    index === editIndex ? updatedCategory : category
                );
                Swal.fire('Success', 'Category updated successfully!', 'success');
                fetchedCategories();
                setCategories(updatedCategories);
                updateLocalStorage(updatedCategories);
                resetForm();
                toggleModal();
            } else {
                const newCategoryData = {
                    ...newCategory,
                    status: newCategory.status === 'Active' || newCategory.status === true,
                };
                console.log('Adding category:', newCategoryData);
                const addedCategory = await addCategory(newCategoryData);
                // Prepend the new category to the existing categories
                const updatedCategories = [addedCategory, ...categories]; // Add the new category at the top
                fetchedCategories();
                setCategories(updatedCategories);
                updateLocalStorage(updatedCategories);
                resetForm();
                toggleModal();
            }
        } catch (error) {
            console.error('Error adding/updating category:', error);
        }
    };

    const handleDelete = async (index) => {
        const categoryToDelete = categories[index];
        console.log('Deleting category:', categoryToDelete);

        Swal.fire({
            title: `Are you sure you want to delete ${categoryToDelete.name}?`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, delete it!',
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const message = await deleteCategory(categoryToDelete.id);
                    //   console.log(licenceToDelete.id);

                    const filteredsegments = categories.filter((_, i) => i !== index);
                    setCategories(filteredsegments);
                    updateLocalStorage(filteredsegments);
                    Swal.fire('Deleted!', message, 'success');
                } catch (error) {
                    console.error('Error deleting service:', error.message);
                    Swal.fire('Error!', error.message, 'error');
                }
            }
        });
    };

    const resetForm = () => {
        setNewCategory({ name: '', status: 'Active' });
        setEditing(false);
        setEditIndex(null);
        setErrors({});
    };

    const validateForm = () => {
        const newErrors = {};
        if (!newCategory.name.trim()) {
            newErrors.name = 'Category name is required';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleEdit = (index) => {
        setNewCategory({ ...categories[index], status: categories[index].status ? 'Active' : 'Inactive' });
        setEditing(true);
        setEditIndex(index);
        toggleModal(false);
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedCategories = [...categories].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setCategories(sortedCategories);
    };

    const filteredCategories = categories.filter((category) => {
        const statusText = category.status ? 'active' : 'inactive';
        return (
            category.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            statusText.includes(searchQuery.toLowerCase())
        );
    });

    const indexOfLastCategory = currentPage * itemsPerPage;
    const indexOfFirstCategory = indexOfLastCategory - itemsPerPage;

    let currentCategories = filteredCategories;

    if (currentPage === 1 && filteredCategories.length > itemsPerPage) {
        const extraItem = filteredCategories[filteredCategories.length - 1];
        currentCategories = [extraItem, ...currentCategories.slice(0, itemsPerPage - 1)];
    }

    const handlePreviousBatch = () => {
        if (pageBatch > 0) setPageBatch(pageBatch - 1);
    };

    const handleNextBatch = () => {
        const maxBatch = Math.ceil(totalPages / pagesPerBatch) - 1;
        if (pageBatch < maxBatch) setPageBatch(pageBatch + 1);
    };

    const handlePageChange = (page) => {
        setCurrentPage(page);
    };

    const handlePrevious = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1);
    };

    const handleNext = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1);
    };

    const startPage = pageBatch * pagesPerBatch + 1;
    const endPage = Math.min(startPage + pagesPerBatch - 1, totalPages);
    const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader className="d-flex justify-content-between align-items-center custom-responsive-style">
                        <div>
                            <h3>Category</h3>
                        </div>
                        <div className='custom-style' style={{ marginLeft: '35%' }}>
                            <Button onClick={toggleModal} className="search-btn-clr">
                                Add Category
                            </Button>
                        </div>
                        <div className="custom-responsive-style-btns" style={{ display: 'flex' }}>
                            <Input
                                type="text"
                                placeholder="Search..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyDown={handleKeyDown}
                                className='custom-input-styles'
                            />
                            <Button className="search-btn-clr text-nowrap" onClick={handleSearchClick}>Search</Button>
                        </div>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th className='custom-col-design'>S.NO</th>
                                            <th onClick={() => handleSort('name')} className='custom-col-design'>Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th onClick={() => handleSort('status')} className='custom-col-design'>Status <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" /></th>
                                            <th className='custom-col-design'>Action</th>
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {currentCategories.length === 0 ? (
                                            <tr>
                                                <td colSpan="4" style={{ textAlign: 'center' }}>
                                                    No Category Found
                                                </td>
                                            </tr>
                                        ) : (
                                            currentCategories.map((category, index) => (
                                                <tr key={index}>
                                                    <td>{indexOfFirstCategory + index + 1}</td>
                                                    <td>{category.name}</td>
                                                    <td>
                                                        <Badge
                                                            pill
                                                            className="status-pill"
                                                            style={{
                                                                padding: '8px',
                                                                border: `1px solid ${category.status ? 'green' : 'red'}`,
                                                                color: category.status ? 'green' : 'red',
                                                                backgroundColor: 'transparent',
                                                            }}
                                                        >
                                                            {category.status ? 'Active' : 'Inactive'}
                                                        </Badge>
                                                    </td>
                                                    <td>
                                                        <FaPencilAlt
                                                            style={{
                                                                cursor: 'pointer',
                                                                marginRight: '10px',
                                                                color: '#6d62e7',
                                                            }}
                                                            onClick={() => handleEdit(index)}
                                                        />
                                                        <FaTrashAlt
                                                            style={{
                                                                cursor: 'pointer',
                                                                color: '#dc3545',
                                                            }}
                                                            onClick={() => handleDelete(index)}
                                                        />
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </Table>
                            </div>

                            <div className={`d-flex justify-content-end align-items-center ${isMobile ? 'gap-0' : 'gap-0'} custom-pagi-style`}>
                                <p className="mb-0 me-2">Rows per page</p>
                                <Input
                                    type="select"
                                    value={itemsPerPage}
                                    onChange={(e) => {
                                        setItemsPerPage(parseInt(e.target.value));
                                        setCurrentPage(1); // Reset to page 1 when changing items per page
                                    }}
                                    style={{ width: '80px' }}
                                    className="me-3"
                                >
                                    <option value="10">10</option>
                                    <option value="25">25</option>
                                    <option value="50">50</option>
                                </Input>

                                <Pagination>
                                    {/* Previous button */}
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink previous onClick={handlePrevious}>
                                            {isMobile ? 'Pre' : 'Previous'}
                                        </PaginationLink>
                                    </PaginationItem>

                                    {/* '<' arrow */}
                                    {pageBatch > 0 && (
                                        <PaginationItem>
                                            <PaginationLink onClick={handlePreviousBatch}>&lt;</PaginationLink>
                                        </PaginationItem>
                                    )}

                                    {/* Page numbers */}
                                    {pages.map((page) => (
                                        <PaginationItem active={page === currentPage} key={page}>
                                            <PaginationLink onClick={() => handlePageChange(page)}>{page}</PaginationLink>
                                        </PaginationItem>
                                    ))}

                                    {/* '>' arrow */}
                                    {endPage < totalPages && (
                                        <PaginationItem>
                                            <PaginationLink onClick={handleNextBatch}>&gt;</PaginationLink>
                                        </PaginationItem>
                                    )}

                                    {/* Next button */}
                                    <PaginationItem disabled={currentPage === totalPages}>
                                        <PaginationLink next onClick={handleNext}>
                                            Next
                                        </PaginationLink>
                                    </PaginationItem>
                                </Pagination>
                            </div>

                        </Col>
                    </div>
                </Card>
            </Col>

            <Modal isOpen={modalOpen} toggle={toggleModal} className='custom-responsive-modal-style'>
                <ModalHeader toggle={toggleModal}>
                    {editing ? 'Edit Category' : 'Add New Category'}
                </ModalHeader>
                <ModalBody>
                    <form onSubmit={handleAddOrEditCategory}>
                        <FormGroup>
                            <Label for="categoryName">Category Name
                                <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                            </Label>
                            <Input
                                id="categoryName"
                                type="text"
                                placeholder="Enter category name"
                                className='custom-input-style'
                                value={newCategory.name}
                                invalid={!!errors.name}
                                onChange={(e) =>
                                    setNewCategory({ ...newCategory, name: e.target.value })
                                }
                            />
                            <FormFeedback>{errors.name}</FormFeedback>
                        </FormGroup>

                        <FormGroup>
                            <Label for="categoryStatus">Status
                                <span style={{ color: 'red', fontSize: '20px' }}>*</span>
                            </Label>
                            <Input
                                id="categoryStatus"
                                type="select"
                                className='custom-input-style'
                                value={newCategory.status}
                                onChange={(e) =>
                                    setNewCategory({ ...newCategory, status: e.target.value })
                                }
                            >
                                <option value="">Select Status</option>
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                            </Input>
                        </FormGroup>

                        <div className="d-flex justify-content-end">
                            <Button className="search-btn-clr" onSubmit={handleAddOrEditCategory}>
                                {editing ? 'Update' : 'Add'}
                            </Button>
                            <Button
                                color="danger"
                                onClick={toggleModal}
                                style={{ marginLeft: '10px' }}
                            >
                                Cancel
                            </Button>
                        </div>
                    </form>
                </ModalBody>
            </Modal>
        </Fragment>
    );
};

export default Category;