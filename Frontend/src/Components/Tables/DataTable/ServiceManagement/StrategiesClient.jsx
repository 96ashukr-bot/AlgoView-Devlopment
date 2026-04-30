import React, { useEffect, useState, Fragment } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { H3 } from '../../../../AbstractElements';
import { FaArrowUp, FaArrowDown } from 'react-icons/fa';
import { RotatingLines } from 'react-loader-spinner';
import './ServiceManagement.css';
import { getSpecificDetails, getSegmentsList } from '../../../../Services/Authentication';

const StrategiesClient = () => {
    const [groupServiceRows, setGroupServiceRows] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [pagesPerGroup] = useState(4);
    const [currentGroup, setCurrentGroup] = useState(1);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [clientDetails, segmentsResponse] = await Promise.all([
                getSpecificDetails(),
                getSegmentsList(),
            ]);

            const segmentList = Array.isArray(segmentsResponse)
                ? segmentsResponse
                : segmentsResponse?.results || [];

            const segmentNameById = segmentList.reduce((map, segment) => {
                map[String(segment.id)] = segment.name;
                return map;
            }, {});

            const groupService = clientDetails?.Group_service;
            const rows = (groupService?.json_data || []).map((entry, index) => ({
                id: index + 1,
                group_name: groupService?.group_name || 'Not Assigned',
                script_name: entry.ScriptName || entry.ServiceName || 'Not Assigned',
                segment_name:
                    segmentNameById[String(entry.segment)] ||
                    groupService?.segment?.name ||
                    'Not Assigned',
                lot_size: entry.LotSize || '-',
                qty: entry.Qty || '-',
                product_type: entry.ProductType || '-',
            }));

            setGroupServiceRows(rows);
        } catch (error) {
            console.error('Error fetching group service:', error);
            setGroupServiceRows([]);
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

        const sortedRows = [...groupServiceRows].sort((a, b) => {
            const firstValue = a[key] ?? '';
            const secondValue = b[key] ?? '';
            if (firstValue < secondValue) return direction === 'asc' ? -1 : 1;
            if (firstValue > secondValue) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        setGroupServiceRows(sortedRows);
    };

    const filteredRows = groupServiceRows.filter((row) =>
        row.group_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        row.script_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        row.segment_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const indexOfLastRow = currentPage * itemsPerPage;
    const indexOfFirstRow = indexOfLastRow - itemsPerPage;
    const currentRows = filteredRows.slice(indexOfFirstRow, indexOfLastRow);
    const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
    const totalGroups = Math.ceil(totalPages / pagesPerGroup);

    const currentGroupPages = Array.from(
        { length: Math.min(pagesPerGroup, Math.max(totalPages - (currentGroup - 1) * pagesPerGroup, 0)) },
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

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center custom-responsive-style">
                            <div>
                                <H3>Group Service</H3>
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
                                            <th onClick={() => handleSort('group_name')} className='custom-col-design'>
                                                Group Service <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('script_name')} className='custom-col-design'>
                                                Script Name <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th onClick={() => handleSort('segment_name')} className='custom-col-design'>
                                                Segment <FaArrowUp className="arrow-icon" /> <FaArrowDown className="arrow-icon" />
                                            </th>
                                            <th className='custom-col-design'>Lot Size</th>
                                            <th className='custom-col-design'>Qty</th>
                                            <th className='custom-col-design'>Product Type</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {loading ? (
                                            <tr>
                                                <td colSpan="7" style={{ textAlign: 'center', height: '100px' }}>
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
                                        ) : currentRows.length > 0 ? (
                                            currentRows.map((row, index) => (
                                                <tr key={`${row.group_name}-${row.script_name}-${index}`}>
                                                    <td>{indexOfFirstRow + index + 1}</td>
                                                    <td>{row.group_name}</td>
                                                    <td>{row.script_name}</td>
                                                    <td>{row.segment_name}</td>
                                                    <td>{row.lot_size}</td>
                                                    <td>{row.qty}</td>
                                                    <td>{row.product_type}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="7" style={{ textAlign: 'center' }}>No Group Service Allotted</td>
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

                                    <PaginationItem disabled={currentGroup === totalGroups || totalPages === 0}>
                                        <PaginationLink onClick={handleNextGroup}>&gt;</PaginationLink>
                                    </PaginationItem>

                                    <PaginationItem disabled={currentPage === totalPages || totalPages === 0}>
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
