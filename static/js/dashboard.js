// 전역 변수
let chart = null;
const teamId = localStorage.getItem('selectedTeamId');
const memberId = localStorage.getItem('currentMemberId');
const memberName = localStorage.getItem('currentMemberName');
const teamName = localStorage.getItem('selectedTeamName');

// 인증 확인
if (!teamId || !memberId) {
    alert('로그인이 필요합니다.');
    window.location.href = '/';
}

// 팀 및 팀원 정보 표시
document.getElementById('teamMemberInfo').textContent = `${teamName} - ${memberName}`;

// 탭 전환
function showTab(tabName) {
    // 모든 탭 숨기기
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // 모든 탭 버튼 비활성화
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 선택된 탭 표시
    const tabs = {
        'dashboard': 'dashboardTab',
        'expenses': 'expensesTab',
        'members': 'membersTab',
        'settings': 'settingsTab'
    };
    
    document.getElementById(tabs[tabName]).style.display = 'block';
    event.target.classList.add('active');
    
    // 각 탭별 데이터 로드
    if (tabName === 'dashboard') {
        loadDashboardData();
    } else if (tabName === 'expenses') {
        loadExpenses();
    } else if (tabName === 'members') {
        loadMembers();
    } else if (tabName === 'settings') {
        loadSettings();
    }
}

// 로그아웃
function logout() {
    localStorage.clear();
    window.location.href = '/';
}

// 대시보드 데이터 로드
async function loadDashboardData() {
    try {
        const [dashboardResponse, teamResponse] = await Promise.all([
            fetch(`/api/auth/dashboard/${teamId}`),
            fetch(`/api/teams/${teamId}`)
        ]);

        if (!dashboardResponse.ok || !teamResponse.ok) {
            throw new Error('대시보드 정보를 불러오는데 실패했습니다.');
        }

        const dashboard = await dashboardResponse.json();
        const team = await teamResponse.json();

        const totalBudget = dashboard.accumulated_budget || 0;
        const totalExpense = dashboard.total_spent || 0;
        const totalSupply = dashboard.supply_amount_spent || 0;
        const totalVAT = dashboard.vat_spent || 0;
        const remainingBudget = dashboard.remaining_budget || 0;
        const remainingBudgetExcludingVAT = dashboard.remaining_budget_without_vat || 0;
        
        // 화면에 표시
        document.getElementById('totalBudget').textContent = totalBudget.toLocaleString() + '원';
        document.getElementById('totalExpense').textContent = totalExpense.toLocaleString() + '원';
        document.getElementById('expenseBreakdown').textContent = 
            `공급: ${totalSupply.toLocaleString()}원 | VAT: ${totalVAT.toLocaleString()}원`;
        document.getElementById('remainingBudget').textContent = remainingBudget.toLocaleString() + '원';
        document.getElementById('remainingBudgetExcludingVAT').textContent = remainingBudgetExcludingVAT.toLocaleString() + '원';
        
        // 현재 정보
        document.getElementById('currentMonth').textContent = dashboard.current_month || '-';
        document.getElementById('budgetCycle').textContent = dashboard.budget_cycle_info || getCycleText(team.budget_cycle);
        document.getElementById('perPersonBudget').textContent = (team.per_person_amount || 0).toLocaleString() + '원';
        document.getElementById('memberCount').textContent = ((team.members || []).length || 0) + '명';
        
        // 팀원별 지출 그래프
        drawMemberExpenseChart(dashboard.member_expenses || []);
        
    } catch (error) {
        console.error('대시보드 데이터 로드 실패:', error);
        alert('데이터를 불러오는데 실패했습니다.');
    }
}

// 사이클 텍스트 변환
function getCycleText(cycle) {
    const cycleMap = {
        'monthly': '월별',
        'quarterly': '분기별',
        'half-yearly': '반기별',
        'yearly': '연도별'
    };
    return cycleMap[cycle] || cycle;
}

// 팀원별 지출 그래프 그리기
function drawMemberExpenseChart(memberExpenses) {
    const ctx = document.getElementById('memberExpenseChart');
    
    // 팀원이 없는 경우 처리
    if (memberExpenses.length === 0) {
        // 기존 차트 제거
        if (chart) {
            chart.destroy();
            chart = null;
        }
        ctx.parentElement.innerHTML = '<p style="text-align: center; padding: 50px; color: #7f8c8d;">팀원을 추가하면 사용 내역이 표시됩니다.</p>';
        return;
    }
    
    // 차트 컨테이너가 텍스트로 변경되었을 경우 캔버스로 복원
    if (!ctx || ctx.tagName !== 'CANVAS') {
        const container = document.querySelector('.chart-container');
        container.innerHTML = '<canvas id="memberExpenseChart"></canvas>';
        return drawMemberExpenseChart(memberExpenses);
    }
    
    const labels = memberExpenses.map(item => item.name);
    const data = memberExpenses.map(item => item.amount || 0);
    
    // 기존 차트 제거
    if (chart) {
        chart.destroy();
    }
    
    // 새 차트 생성
    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '지출액 (원)',
                data: data,
                backgroundColor: 'rgba(74, 144, 226, 0.7)',
                borderColor: 'rgba(74, 144, 226, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString() + '원';
                        }
                    }
                }
            }
        }
    });
}

// 지출 내역 로드
async function loadExpenses() {
    try {
        const response = await fetch(`/api/expenses?team_id=${teamId}`);
        const expenses = await response.json();
        
        // 팀원 정보도 가져오기
        const membersResponse = await fetch(`/api/members/${teamId}`);
        const members = await membersResponse.json();
        const memberMap = {};
        members.forEach(m => memberMap[m.id] = m.name);
        
        const expenseList = document.getElementById('expenseList');
        expenseList.innerHTML = '';
        
        if (expenses.length === 0) {
            expenseList.innerHTML = '<tr><td colspan="8" class="text-center">등록된 지출 내역이 없습니다.</td></tr>';
        } else {
            expenses.reverse().forEach(expense => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(expense.created_at).toLocaleDateString()}</td>
                    <td>${memberMap[expense.member_id] || '알 수 없음'}</td>
                    <td><span class="badge badge-primary">${expense.category}</span></td>
                    <td>${expense.description || '-'}</td>
                    <td>${expense.supply_amount.toLocaleString()}원</td>
                    <td>${expense.vat.toLocaleString()}원</td>
                    <td><strong>${expense.total_amount.toLocaleString()}원</strong></td>
                    <td>
                        <button class="btn btn-danger" onclick="deleteExpense('${expense.id}')" style="padding: 5px 10px; font-size: 0.9rem;">삭제</button>
                    </td>
                `;
                expenseList.appendChild(row);
            });
        }
    } catch (error) {
        console.error('지출 내역 로드 실패:', error);
    }
}

// VAT 계산
function calculateVAT() {
    const totalAmount = parseFloat(document.getElementById('expenseAmount').value) || 0;
    const supplyAmount = Math.floor(totalAmount / 1.1);
    const vatAmount = totalAmount - supplyAmount;
    
    document.getElementById('supplyAmount').textContent = supplyAmount.toLocaleString();
    document.getElementById('vatAmount').textContent = vatAmount.toLocaleString();
}

// 지출 추가 모달
function showAddExpenseModal() {
    document.getElementById('addExpenseModal').classList.add('active');
}

function closeAddExpenseModal() {
    document.getElementById('addExpenseModal').classList.remove('active');
    document.getElementById('addExpenseForm').reset();
    document.getElementById('supplyAmount').textContent = '0';
    document.getElementById('vatAmount').textContent = '0';
}

// 지출 추가
document.getElementById('addExpenseForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (memberId === 'admin') {
        alert('관리자 모드에서는 지출을 등록할 수 없습니다. 팀원을 추가한 뒤 팀원으로 로그인해주세요.');
        return;
    }
    
    const totalAmount = parseInt(document.getElementById('expenseAmount').value);
    
    const expenseData = {
        team_id: teamId,
        member_id: memberId,
        category: document.getElementById('expenseCategory').value,
        description: document.getElementById('expenseDescription').value || "",
        total_amount: totalAmount
    };
    
    try {
        const response = await fetch('/api/expenses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(expenseData)
        });
        
        if (response.ok) {
            closeAddExpenseModal();
            loadExpenses();
            loadDashboardData();
            alert('지출이 추가되었습니다.');
        } else {
            const error = await response.json().catch(() => ({}));
            const errorMessage = error.detail || '지출 추가에 실패했습니다.';
            alert(errorMessage);
        }
    } catch (error) {
        console.error('지출 추가 실패:', error);
        alert('지출 추가 중 오류가 발생했습니다.');
    }
});

// 지출 삭제
async function deleteExpense(expenseId) {
    if (!confirm('이 지출 내역을 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/expenses/${expenseId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadExpenses();
            loadDashboardData();
            alert('지출 내역이 삭제되었습니다.');
        } else {
            alert('삭제에 실패했습니다.');
        }
    } catch (error) {
        console.error('지출 삭제 실패:', error);
        alert('삭제 중 오류가 발생했습니다.');
    }
}

// 팀원 목록 로드
async function loadMembers() {
    try {
        const response = await fetch(`/api/members/${teamId}`);
        const members = await response.json();
        
        const memberList = document.getElementById('memberList');
        memberList.innerHTML = '';
        
        if (members.length === 0) {
            memberList.innerHTML = '<tr><td colspan="3" class="text-center">등록된 팀원이 없습니다.</td></tr>';
        } else {
            members.forEach(member => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${member.name}</strong></td>
                    <td>${member.created_at ? new Date(member.created_at).toLocaleDateString() : '-'}</td>
                    <td>
                        <button class="btn btn-warning" onclick="updateMember('${member.id}', '${member.name.replace(/'/g, "\\'")}')" style="padding: 5px 10px; font-size: 0.9rem; margin-right: 6px;">수정</button>
                        <button class="btn btn-danger" onclick="deleteMember('${member.id}')" style="padding: 5px 10px; font-size: 0.9rem;">삭제</button>
                    </td>
                `;
                memberList.appendChild(row);
            });
        }
    } catch (error) {
        console.error('팀원 목록 로드 실패:', error);
    }
}

// 팀원 추가 모달
function showAddMemberModal() {
    document.getElementById('addMemberModal').classList.add('active');
}

function closeAddMemberModal() {
    document.getElementById('addMemberModal').classList.remove('active');
    document.getElementById('addMemberForm').reset();
}

// 팀원 추가
document.getElementById('addMemberForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const memberData = {
        name: document.getElementById('memberName').value
    };
    
    try {
        const response = await fetch(`/api/members/${teamId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(memberData)
        });
        
        if (response.ok) {
            closeAddMemberModal();
            loadMembers();
            loadDashboardData();
            alert('팀원이 추가되었습니다.');
        } else {
            const error = await response.json();
            alert('팀원 추가에 실패했습니다: ' + (error.detail || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('팀원 추가 실패:', error);
        alert('팀원 추가 중 오류가 발생했습니다.');
    }
});

// 팀원 삭제
async function deleteMember(memberId) {
    if (!confirm('이 팀원을 삭제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/members/${teamId}/${memberId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadMembers();
            loadDashboardData();
            alert('팀원이 삭제되었습니다.');
        } else {
            const error = await response.json();
            alert('삭제에 실패했습니다: ' + (error.detail || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('팀원 삭제 실패:', error);
        alert('삭제 중 오류가 발생했습니다.');
    }
}

// 팀원 수정
async function updateMember(memberId, currentName) {
    const newName = prompt('새 팀원 이름을 입력하세요.', currentName);
    if (!newName) {
        return;
    }

    const trimmedName = newName.trim();
    if (!trimmedName || trimmedName === currentName) {
        return;
    }

    try {
        const response = await fetch(`/api/members/${teamId}/${memberId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: trimmedName })
        });

        if (response.ok) {
            alert('팀원 정보가 수정되었습니다.');
            loadMembers();
            loadDashboardData();
            return;
        }

        const error = await response.json();
        alert('수정에 실패했습니다: ' + (error.detail || '알 수 없는 오류'));
    } catch (error) {
        console.error('팀원 수정 실패:', error);
        alert('수정 중 오류가 발생했습니다.');
    }
}

// 설정 로드
async function loadSettings() {
    try {
        const response = await fetch(`/api/teams/${teamId}`);
        const team = await response.json();
        
        document.getElementById('settingsPerPersonBudget').value = team.per_person_amount || 0;
        document.getElementById('settingsResetCycle').value = team.budget_cycle || 'monthly';
    } catch (error) {
        console.error('설정 로드 실패:', error);
    }
}

// 설정 저장
document.getElementById('settingsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const settingsData = {
        per_person_amount: parseInt(document.getElementById('settingsPerPersonBudget').value),
        budget_cycle: document.getElementById('settingsResetCycle').value
    };
    
    try {
        const response = await fetch(`/api/settings/${teamId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settingsData)
        });
        
        if (response.ok) {
            alert('설정이 저장되었습니다.');
            loadDashboardData();
        } else {
            const error = await response.json();
            const errorMsg = error.detail ? 
                (Array.isArray(error.detail) ? error.detail.map(e => e.msg).join(', ') : error.detail) 
                : '알 수 없는 오류';
            alert('설정 저장에 실패했습니다: ' + errorMsg);
        }
    } catch (error) {
        console.error('설정 저장 실패:', error);
        alert('설정 저장 중 오류가 발생했습니다.');
    }
});

// 데이터 다운로드
async function downloadData() {
    try {
        const response = await fetch(`/api/settings/${teamId}/download-expenses`);
        if (!response.ok) {
            throw new Error('데이터 다운로드 실패');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        const contentDisposition = response.headers.get('content-disposition') || '';
        const filenameMatch = contentDisposition.match(/filename="?([^\"]+)"?/);
        a.download = filenameMatch ? filenameMatch[1] : `budgetpro_${teamName}_${new Date().toISOString().split('T')[0]}.json`;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        alert('데이터가 다운로드되었습니다.');
    } catch (error) {
        console.error('데이터 다운로드 실패:', error);
        alert('다운로드 중 오류가 발생했습니다.');
    }
}

// 데이터 업로드
async function uploadData(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`/api/settings/${teamId}/upload-expenses`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(result.message || '데이터가 복구되었습니다.');
            loadDashboardData();
            loadExpenses();
            loadMembers();
        } else {
            const error = await response.json();
            alert('데이터 복구에 실패했습니다: ' + (error.detail || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('데이터 업로드 실패:', error);
        alert('업로드 중 오류가 발생했습니다.');
    } finally {
        // 파일 입력 초기화
        event.target.value = '';
    }
}

// 데이터 초기화
async function resetData() {
    if (!confirm('모든 지출 정보가 삭제됩니다. 계속하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/settings/${teamId}/reset-budget`, {
            method: 'POST'
        });
        
        if (response.ok) {
            alert('지출 정보가 초기화되었습니다.');
            loadDashboardData();
            loadExpenses();
        } else {
            alert('초기화에 실패했습니다.');
        }
    } catch (error) {
        console.error('데이터 초기화 실패:', error);
        alert('초기화 중 오류가 발생했습니다.');
    }
}

// 페이지 로드 시 대시보드 데이터 로드
loadDashboardData();
