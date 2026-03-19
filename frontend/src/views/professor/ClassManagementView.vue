<template>
  <div class="page container">
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
      <button class="btn btn-outline" @click="$router.push('/professor')" style="padding: 8px 14px; font-size: 13px;">
        &larr; Inapoi
      </button>
      <h1 class="page-title" style="margin-bottom: 0;">Gestionare Clase</h1>
    </div>
    <p class="page-subtitle">Creeaza clase, adauga studenti si genereaza link-uri de invitatie</p>

    <!-- Create Class -->
    <div class="card" style="margin-bottom: 24px;">
      <h3 style="font-weight: 700; margin-bottom: 16px;">Creeaza o clasa noua</h3>
      <form @submit.prevent="createClass" style="display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap;">
        <div class="form-group" style="flex: 1; min-width: 200px; margin-bottom: 0;">
          <label>Numele clasei</label>
          <input v-model="newClassName" class="form-input" placeholder="ex: 1401A" required />
        </div>
        <button type="submit" class="btn btn-primary">Creeaza clasa</button>
      </form>
      <div v-if="createMsg" style="margin-top: 10px; font-size: 13px; color: var(--success);">{{ createMsg }}</div>
    </div>

    <!-- Classes Grid -->
    <div v-if="loading" style="text-align: center; padding: 60px; color: var(--text-muted);">
      Se incarca...
    </div>

    <div v-else-if="classes.length === 0" style="text-align: center; padding: 60px; color: var(--text-muted);">
      Nu exista clase inregistrate. Creeaza prima clasa mai sus.
    </div>

    <div v-else class="grid-2">
      <div
        v-for="cls in classes"
        :key="cls.group_name"
        class="card"
        style="cursor: pointer;"
        @click="selectClass(cls.group_name)"
        :style="selectedClass === cls.group_name ? 'border-color: var(--accent);' : ''"
      >
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <h4 style="font-weight: 700; font-size: 18px;">{{ cls.group_name }}</h4>
          <span class="badge" style="background: rgba(108, 92, 231, 0.15); color: var(--accent);">
            {{ cls.student_count }} studenti
          </span>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 12px;">
          <button class="btn btn-outline" style="font-size: 12px; padding: 6px 12px;" @click.stop="selectClass(cls.group_name)">
            Vezi studenti
          </button>
          <button class="btn btn-primary" style="font-size: 12px; padding: 6px 12px;" @click.stop="generateInvite(cls.group_name)">
            Link invitatie
          </button>
        </div>
      </div>
    </div>

    <!-- Invite Link Display -->
    <div v-if="inviteInfo" class="card" style="margin-top: 24px; border-color: var(--accent);">
      <h4 style="font-weight: 700; margin-bottom: 12px;">Link Invitatie - {{ inviteInfo.group_name }}</h4>
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 200px;">
          <label style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Cod invitatie</label>
          <div style="font-size: 20px; font-weight: 800; color: var(--accent); font-family: 'Courier New', monospace; letter-spacing: 2px; margin-top: 4px;">
            {{ inviteInfo.invite_code }}
          </div>
        </div>
        <div style="flex: 2; min-width: 300px;">
          <label style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Link complet</label>
          <div style="background: var(--bg-secondary); padding: 10px 14px; border-radius: var(--radius-sm); font-size: 13px; color: var(--text-secondary); margin-top: 4px; word-break: break-all;">
            {{ window.location.origin }}{{ inviteInfo.invite_link }}
          </div>
        </div>
        <button class="btn btn-success" @click="copyInviteLink" style="font-size: 12px;">
          {{ copied ? 'Copiat!' : 'Copiaza' }}
        </button>
      </div>
    </div>

    <!-- Selected Class Detail -->
    <div v-if="selectedClass" class="card" style="margin-top: 24px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h3 style="font-weight: 700;">Studenti - {{ selectedClass }}</h3>
        <button class="btn btn-outline" style="font-size: 12px; padding: 6px 12px;" @click="selectedClass = null">Inchide</button>
      </div>

      <!-- Add Student Form -->
      <div style="background: var(--bg-secondary); border-radius: var(--radius-sm); padding: 16px; margin-bottom: 20px;">
        <h4 style="font-weight: 600; margin-bottom: 12px; font-size: 14px; color: var(--text-secondary);">Adauga student nou</h4>
        <form @submit.prevent="addStudent" style="display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end;">
          <div class="form-group" style="flex: 1; min-width: 150px; margin-bottom: 0;">
            <label>Username</label>
            <input v-model="newStudent.username" class="form-input" placeholder="ex: ion.popescu" required />
          </div>
          <div class="form-group" style="flex: 1; min-width: 150px; margin-bottom: 0;">
            <label>Nume complet</label>
            <input v-model="newStudent.full_name" class="form-input" placeholder="ex: Ion Popescu" required />
          </div>
          <div class="form-group" style="flex: 1; min-width: 200px; margin-bottom: 0;">
            <label>Email</label>
            <input v-model="newStudent.email" type="email" class="form-input" placeholder="ex: ion@student.tuiasi.ro" required />
          </div>
          <button type="submit" class="btn btn-success" :disabled="addingStudent">
            {{ addingStudent ? 'Se adauga...' : 'Adauga' }}
          </button>
        </form>
        <div v-if="addStudentMsg" style="margin-top: 10px; font-size: 13px;" :style="{ color: addStudentError ? 'var(--danger)' : 'var(--success)' }">
          {{ addStudentMsg }}
        </div>
        <div v-if="generatedPassword" style="margin-top: 8px; padding: 10px; background: var(--bg-card); border-radius: var(--radius-sm); border: 1px solid var(--accent);">
          <span style="font-size: 12px; color: var(--text-muted);">Parola generata:</span>
          <span style="font-weight: 700; color: var(--accent); font-family: 'Courier New', monospace; margin-left: 8px; font-size: 16px;">{{ generatedPassword }}</span>
          <span style="font-size: 11px; color: var(--text-muted); margin-left: 8px;">(comunicati-o studentului)</span>
        </div>
      </div>

      <!-- Students List -->
      <div v-if="studentsLoading" style="text-align: center; padding: 30px; color: var(--text-muted);">
        Se incarca studentii...
      </div>

      <div v-else-if="students.length === 0" style="text-align: center; padding: 30px; color: var(--text-muted);">
        Niciun student in aceasta clasa.
      </div>

      <div v-else style="border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden;">
        <table class="data-table">
          <thead>
            <tr>
              <th>Nume</th>
              <th>Username</th>
              <th>Email</th>
              <th>Jocuri</th>
              <th>Scor mediu</th>
              <th>Victorii</th>
              <th>Actiuni</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td style="font-weight: 600;">{{ s.full_name }}</td>
              <td><code>{{ s.username }}</code></td>
              <td style="font-size: 12px; color: var(--text-secondary);">{{ s.email }}</td>
              <td>{{ s.games_played }}</td>
              <td>
                <span :style="{ color: s.avg_score > 0 ? 'var(--accent)' : 'var(--text-muted)' }">
                  {{ s.avg_score }}
                </span>
              </td>
              <td>
                <span :style="{ color: s.wins > 0 ? 'var(--gold)' : 'var(--text-muted)' }">
                  {{ s.wins }}
                </span>
              </td>
              <td>
                <div style="display: flex; gap: 4px; align-items: center; flex-wrap: wrap;">
                  <select
                    class="form-select"
                    style="font-size: 11px; padding: 3px 6px; min-width: 90px;"
                    @change="moveStudent(s.id, s.full_name, $event.target.value); $event.target.value = ''"
                  >
                    <option value="">Mută în...</option>
                    <option v-for="cls in classes.filter(c => c.group_name !== selectedClass)" :key="cls.group_name" :value="cls.group_name">
                      {{ cls.group_name }}
                    </option>
                  </select>
                  <button
                    class="btn btn-danger"
                    style="font-size: 11px; padding: 4px 10px;"
                    @click="removeStudent(s.id, s.full_name)"
                  >
                    Elimina
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const classes = ref([])
const loading = ref(true)
const createMsg = ref('')
const newClassName = ref('')

const selectedClass = ref(null)
const students = ref([])
const studentsLoading = ref(false)

const newStudent = ref({ username: '', full_name: '', email: '' })
const addingStudent = ref(false)
const addStudentMsg = ref('')
const addStudentError = ref(false)
const generatedPassword = ref('')

const inviteInfo = ref(null)
const copied = ref(false)

const window = globalThis.window

async function loadClasses() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/classes')
    classes.value = data
  } catch (e) {
    console.error('Failed to load classes:', e)
  } finally {
    loading.value = false
  }
}

async function createClass() {
  if (!newClassName.value.trim()) return
  try {
    const { data } = await api.post('/admin/classes', { group_name: newClassName.value.trim() })
    createMsg.value = data.message
    newClassName.value = ''
    await loadClasses()
    setTimeout(() => { createMsg.value = '' }, 3000)
  } catch (e) {
    createMsg.value = 'Eroare: ' + (e.response?.data?.detail || 'Nu s-a putut crea clasa')
  }
}

async function selectClass(groupName) {
  selectedClass.value = groupName
  studentsLoading.value = true
  generatedPassword.value = ''
  addStudentMsg.value = ''
  try {
    const { data } = await api.get(`/admin/classes/${encodeURIComponent(groupName)}/students`)
    students.value = data
  } catch (e) {
    console.error('Failed to load students:', e)
    students.value = []
  } finally {
    studentsLoading.value = false
  }
}

async function addStudent() {
  if (!newStudent.value.username || !newStudent.value.full_name || !newStudent.value.email) return
  addingStudent.value = true
  addStudentMsg.value = ''
  addStudentError.value = false
  generatedPassword.value = ''
  try {
    const { data } = await api.post(`/admin/classes/${encodeURIComponent(selectedClass.value)}/students`, newStudent.value)
    addStudentMsg.value = data.message
    generatedPassword.value = data.generated_password
    newStudent.value = { username: '', full_name: '', email: '' }
    await selectClass(selectedClass.value)
    await loadClasses()
  } catch (e) {
    addStudentMsg.value = 'Eroare: ' + (e.response?.data?.detail || 'Nu s-a putut adauga studentul')
    addStudentError.value = true
  } finally {
    addingStudent.value = false
  }
}

async function moveStudent(userId, name, newGroup) {
  if (!newGroup) return
  if (!confirm(`Muți studentul "${name}" din ${selectedClass.value} în ${newGroup}?`)) return
  try {
    await api.put(`/admin/classes/${encodeURIComponent(selectedClass.value)}/students/${userId}/move`, { new_group: newGroup })
    await selectClass(selectedClass.value)
    await loadClasses()
  } catch (e) {
    alert('Eroare: ' + (e.response?.data?.detail || 'Nu s-a putut muta studentul'))
  }
}

async function removeStudent(userId, name) {
  if (!confirm(`Eliminati studentul "${name}" din clasa ${selectedClass.value}?`)) return
  try {
    await api.delete(`/admin/classes/${encodeURIComponent(selectedClass.value)}/students/${userId}`)
    await selectClass(selectedClass.value)
    await loadClasses()
  } catch (e) {
    alert('Eroare: ' + (e.response?.data?.detail || 'Nu s-a putut elimina studentul'))
  }
}

async function generateInvite(groupName) {
  try {
    const { data } = await api.post('/admin/invite-link', { group_name: groupName })
    inviteInfo.value = data
    copied.value = false
  } catch (e) {
    alert('Eroare la generarea link-ului')
  }
}

function copyInviteLink() {
  if (!inviteInfo.value) return
  const fullLink = window.location.origin + inviteInfo.value.invite_link
  navigator.clipboard.writeText(fullLink).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  })
}

onMounted(loadClasses)
</script>

<style scoped>
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 10px 14px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.data-table td {
  padding: 10px 14px;
  font-size: 13px;
  border-bottom: 1px solid var(--border);
}

.data-table tr:hover td {
  background: var(--bg-card-hover);
}

.data-table tr:last-child td {
  border-bottom: none;
}
</style>
