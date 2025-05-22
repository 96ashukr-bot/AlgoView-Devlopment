import React, { useEffect, useState, Fragment } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { FaArrowUp, FaArrowDown, FaEye } from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { RotatingLines } from 'react-loader-spinner';
import './ServiceManagement.css';
import { getSpecificDetails } from '../../../../Services/Authentication';

const StrategiesClient = () => {
    const [strategies, setStrategies] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [pagesPerGroup] = useState(4);
    const [currentGroup, setCurrentGroup] = useState(1);
    const navigate = useNavigate();

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const response = await getSpecificDetails();
            setStrategies(response.Strategy.map(strategy => ({
                id: strategy.id,
                name: strategy.name,
                description: strategy.description,
            })));
        } catch (error) {
            console.error('Error fetching strategies:', error);
        } finally {
            setLoading(false);
        }
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
        strategy.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastStrategy = currentPage * itemsPerPage;
    const indexOfFirstStrategy = indexOfLastStrategy - itemsPerPage;
    const currentStrategies = filteredStrategies.slice(indexOfFirstStrategy, indexOfLastStrategy);
    const totalPages = Math.ceil(filteredStrategies.length / itemsPerPage);

    const totalGroups = Math.ceil(totalPages / pagesPerGroup);

    const currentGroupPages = Array.from(
        { length: Math.min(pagesPerGroup, totalPages - (currentGroup - 1) * pagesPerGroup) },
        (_, idx) => (currentGroup - 1) * pagesPerGroup + idx + 1
    );

    const handlePreviousGroup = () => {
        if (currentGroup > 1) {
            setCurrentGroup(currentGroup - 1);
            setCurrentPage((currentGroup - 2) * pagesPerGroup + 1);
        }
    };

    const handleNextGroup = () => {
        if (currentGroup < totalGroups) {
            setCurrentGroup(currentGroup + 1);
            setCurrentPage(currentGroup * pagesPerGroup + 1);
        }
    };

    const handleViewClick = (id) => {
        navigate(`/service-manage/client-strategies/view-strategies/${id}`);
    };

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
                                            <th className='custom-col-design'>View</th>
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
                                                <tr key={index}>
                                                    <td>{indexOfFirstStrategy + index + 1}</td>
                                                    <td>{strategy.name}</td>
                                                    <td>{strategy.description || 'N/A'}</td>
                                                    <td>
                                                        <FaEye
                                                            className="view-icon"
                                                            style={{ cursor: 'pointer', fontSize: '20px', marginLeft: '10px' }}
                                                            onClick={() => handleViewClick(strategy.id)}
                                                        />
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="4" style={{ textAlign: 'center' }}>No Strategies Found</td>
                                            </tr>
                                        )}
                                    </tbody>

                                </Table>
                            </div>

                            <div className="d-flex justify-content-end custom-pagi-style">
                                <Pagination>
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                                            Previous
                                        </PaginationLink>
                                    </PaginationItem>

                                    <PaginationItem disabled={currentGroup === 1}>
                                        <PaginationLink onClick={handlePreviousGroup}>&lt;</PaginationLink>
                                    </PaginationItem>

                                    {currentGroupPages.map((page) => (
                                        <PaginationItem key={page} active={page === currentPage}>
                                            <PaginationLink onClick={() => setCurrentPage(page)}>
                                                {page}
                                            </PaginationLink>
                                        </PaginationItem>
                                    ))}

                                    <PaginationItem disabled={currentGroup === totalGroups}>
                                        <PaginationLink onClick={handleNextGroup}>&gt;</PaginationLink>
                                    </PaginationItem>

                                    <PaginationItem disabled={currentPage === totalPages}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage + 1)}>
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

export default StrategiesClient;
