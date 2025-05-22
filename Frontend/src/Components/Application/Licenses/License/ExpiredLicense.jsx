import React, { Fragment, useState } from 'react';
import {
    Col, Card, Table, CardHeader,
    Pagination, PaginationItem, PaginationLink,
    Input, Button
} from 'reactstrap';
import './License.css';

const ExpiredLicense = () => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(10);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: 'clientName', direction: 'asc' });

    const mockData = [
        // { clientName: 'John Doe', email: 'john@example.com', phone: '123-456-7890', startDate: '2024-01-01', endDate: '2024-10-12' },
        // { clientName: 'Jane Smith', email: 'jane@example.com', phone: '987-654-3210', startDate: '2024-02-01', endDate: '2024-10-10' },
        // { clientName: 'Alex Johnson', email: 'alex@example.com', phone: '555-123-4567', startDate: '2024-03-01', endDate: '2024-10-09' },
    ];

    // Sorting function
    const sortedData = [...mockData].sort((a, b) => {
        const { key, direction } = sortConfig;
        const aValue = a[key].toLowerCase ? a[key].toLowerCase() : a[key];
        const bValue = b[key].toLowerCase ? b[key].toLowerCase() : b[key];

        if (aValue < bValue) return direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    const filteredLicenses = sortedData.filter(item =>
        item.clientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.phone.includes(searchQuery)
    );

    const indexOfLastLicense = currentPage * itemsPerPage;
    const indexOfFirstLicense = indexOfLastLicense - itemsPerPage;
    const currentLicenses = filteredLicenses.slice(indexOfFirstLicense, indexOfLastLicense);
    const totalPages = Math.ceil(filteredLicenses.length / itemsPerPage);

    // Update sorting state
    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    // Render sort arrow
    const renderSortArrow = (key) => {
        if (sortConfig.key !== key) return null;
        return sortConfig.direction === 'asc' ? '↑' : '↓';
    };

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <h3>Expired License</h3>
                                {/* <span>{"Below is the list of expired licenses along with their details."}</span> */}
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
                        <Col sm="12" lg="12" xl="12">
                            <div className="table-responsive-sm">
                                <Table>
                                    <thead>
                                        <tr>
                                            <th style={{ backgroundColor: '#283F7B', color: 'white' }}>Sr.No</th>
                                            <th
                                                style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer' }}
                                                // onClick={() => handleSort('clientName')}
                                            >
                                                Client Name {renderSortArrow('clientName')}
                                            </th>
                                            <th
                                                style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer' }}
                                                // onClick={() => handleSort('email')}
                                            >
                                                Email {renderSortArrow('email')}
                                            </th>
                                            <th
                                                style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer' }}
                                                // onClick={() => handleSort('phone')}
                                            >
                                                Phone No. {renderSortArrow('phone')}
                                            </th>
                                            <th
                                                style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer' }}
                                                // onClick={() => handleSort('startDate')}
                                            >
                                                Start Date {renderSortArrow('startDate')}
                                            </th>
                                            <th
                                                style={{ backgroundColor: '#283F7B', color: 'white', cursor: 'pointer' }}
                                                // onClick={() => handleSort('endDate')}
                                            >
                                                End Date {renderSortArrow('endDate')}
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {currentLicenses.map((license, index) => (
                                            <tr key={index}>
                                                <td>{indexOfFirstLicense + index + 1}</td>
                                                <td>{license.clientName}</td>
                                                <td>{license.email}</td>
                                                <td>{license.phone}</td>
                                                <td>{license.startDate}</td>
                                                <td>{license.endDate}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            </div>

                            {/* Pagination */}
                            <div className="d-flex justify-content-end custom-pagi-style">
                                <Pagination>
                                    <PaginationItem disabled={currentPage === 1}>
                                        <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                                            Previous
                                        </PaginationLink>
                                    </PaginationItem>
                                    {[...Array(totalPages)].map((_, index) => (
                                        <PaginationItem key={index} active={index + 1 === currentPage}>
                                            <PaginationLink onClick={() => setCurrentPage(index + 1)}>
                                                {index + 1}
                                            </PaginationLink>
                                        </PaginationItem>
                                    ))}
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

export default ExpiredLicense;
