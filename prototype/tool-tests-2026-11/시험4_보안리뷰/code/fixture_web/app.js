const list = document.getElementById("list");
const input = document.getElementById("title");
const layer = document.querySelector(".toast-layer");

function toast(msg) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  layer.appendChild(el);
  setTimeout(() => el.remove(), 1500);
}

document.getElementById("add-btn").addEventListener("click", () => {
  const title = input.value.trim();
  if (!title) return toast("할 일을 입력하세요");
  const li = document.createElement("li");
  li.textContent = title;
  list.appendChild(li);
  input.value = "";
  toast("추가했어요");
});
