import React, { useEffect, useState, Fragment } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { FaUser, FaEdit, FaPlus, FaArrowUp, FaArrowDown, FaPencilAlt, FaTrashAlt } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { RotatingLines } from 'react-loader-spinner';
import { getStrategies, deleteStrategies } from '../../../../Services/Authentication';
import Swal from 'sweetalert2';
import './ServiceManagement.css'

const Strategies = () => {
    const [strategies, setStrategies] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [totalPages, setTotalPages] = useState([]);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();
    const [isMobile, setIsMobile] = useState(false);
    const [pageBatch, setPageBatch] = useState(0);

    useEffect(() => {
        fetchData();

        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);

    }, [currentPage, itemsPerPage]);

    const pagesPerBatch = isMobile ? 2 : 4;

    const fetchData = async () => {
        try {
            setLoading(true);
            const response = await getStrategies(currentPage, itemsPerPage);

            if (response.results && response.results.length > 0) {
                setStrategies(response.results); // Directly store the paginated data.
                setTotalPages(Math.ceil(response.count / itemsPerPage));
            } else {
                setStrategies([]); // Handle empty pages.
            }
        } catch (err) {
            console.error("Error fetching data:", err);
            setError("Failed to load data.");
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteClick = async (id) => {
        Swal.fire({
            title: 'Are you sure want to delete ?',
            // text: 'This action will delete the strategy permanently!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, delete it!',
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    await deleteStrategies(id);
                    fetchData(); // Refresh the list after deletion
                    Swal.fire('Deleted!', 'The strategy has been deleted successfully.', 'success');
                } catch (error) {
                    console.error('Error deleting strategy:', error);
                    Swal.fire('Error!', 'Failed to delete the strategy.', 'error');
                }
            }
        });
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });

        const sortedStrategies = [...strategies].sort((a, b) => {
            if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
            if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setStrategies(sortedStrategies);
    };

    const filteredStrategies = strategies.filter(strategy =>
        strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        strategy.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        strategy.segment?.short_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastStrategy = currentPage * itemsPerPage;
    const indexOfFirstStrategy = indexOfLastStrategy - itemsPerPage;

    const currentStrategies = filteredStrategies;

    if (currentPage === 1 && filteredStrategies.length > itemsPerPage) {
        const extraItem = filteredStrategies[filteredStrategies.length - 1];
        currentStrategies = [extraItem, ...currentStrategies.slice(0, itemsPerPage - 1)];
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

    const handleEditClick = (id) => navigate(`/service-manage/strategies/editstrategies/${id}`);
    const handleUserClick = (id) => navigate(`/service-manage/strategies/assigned-strategies/${id}`);
    const handleUpdateClick = (id) => navigate(`/service-manage/strategies/updatestrategies/${id}`);

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>Strategies</H3>
                                {/* <span>Below is the list of trade strategies along with their details.</span> */}
                            </div>
                            <div>
                                <button className="btn btn-primary search-btn-clr custom-responsive-style-btn" onClick={() => navigate('/service-manage/add-strategies')} style={{ marginRight: '20px' }}>
                                    Add New Strategies
                                </button>
                                <Input
                                    type="text"
                                    placeholder="Search..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                                />
                                <Button className='search-btn-clr'>Search</Button>
                            </div>
                        </div>
                    </CardHeader>
                    <div className="card-block row">
                        <Col sm="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th className='custom-col-design'>Sr.No</th>
                                            <th onClick={() => handleSort('name')} className='custom-col-design'>
                                                Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('description')} className='custom-col-design'>
                                                Description <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('segment')} className='custom-col-design'>
                                                Segment <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th className='custom-col-design'>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {loading ? (
                                            <tr>
                                                <td colSpan="6" style={{ textAlign: 'center', height: '100px' }}>
                                                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                                        <RotatingLines
                                                            strokeColor="#283F7B"
                                                            strokeWidth="4"
                                                            animationDuration="0.75"
                                                            width="50"
                                                            visible={true}
                                                        />
                                                    </div>
                                                </td>
                                            </tr>
                                        ) : currentStrategies.length > 0 ? (
                                            currentStrategies.map((strategy, index) => (
                                                <tr key={strategy.id}>
                                                    <td>{indexOfFirstStrategy + index + 1}</td>
                                                    <td>{strategy.name}</td>
                                                    <td>{strategy.description || 'N/A'}</td>
                                                    <td>{strategy.segment?.short_name || 'N/A'}</td>
                                                    <td>
                                                        <FaUser
                                                            title="Profile"
                                                            style={{ marginRight: '12px', cursor: 'pointer' }}
                                                            onClick={() => handleUserClick(strategy.id)}
                                                        />
                                                        <FaPencilAlt
                                                            title="Edit"
                                                            style={{ marginRight: '12px', cursor: 'pointer', color: '#6d62e7' }}
                                                            onClick={() => handleEditClick(strategy.id)}
                                                        />
                                                        <FaTrashAlt
                                                            title="Delete"
                                                            style={{ marginRight: '12px', cursor: 'pointer', color: '#ef3636' }}
                                                            onClick={() => handleDeleteClick(strategy.id)}
                                                        />
                                                        <FaPlus
                                                            title="Add"
                                                            style={{ cursor: 'pointer', color: 'green' }}
                                                            onClick={() => handleUpdateClick(strategy.id)}
                                                        />
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="5" style={{ textAlign: 'center' }}>No Strategies Found</td>
                                            </tr>
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
        </Fragment>
    );
};

export default Strategies;
