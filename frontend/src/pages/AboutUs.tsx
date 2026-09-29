import Reveal from '../components/Reveal'
import './AboutUs.css'

export default function AboutUs() {
  return (
    <div className="about-page">
      <div className="container about-hero">
        <p className="eyebrow">Our story</p>
        <h1>About Campus Customs</h1>
      </div>

      <div className="container about-grid">
        <Reveal className="about-copy">
          <p>
            Campus Customs started as a small stand near campus selling Yale crewnecks out of a
            duffel bag on move-in weekend. These days we run a proper storefront in New Haven,
            but the idea hasn't changed: give students, families, and alumni a straightforward
            way to find Yale gear that fits well and holds up through four years (or forty).
          </p>
          <p>
            We stock hoodies, tees, and outerwear for every residential college, plus varsity and
            club sports lines, so there's something for first-years, seniors, and proud parents
            alike. Everything on this site is pulled from the same inventory system our shop
            floor uses, which is also what powers the chat assistant in the corner — ask it about
            sizing or stock and it's reading the same numbers we are.
          </p>
          <p>
            We're based in New Haven, Connecticut, a short walk from campus, and we ship anywhere
            in the country when you can't make it in person.
          </p>
        </Reveal>
        <Reveal delay={120} className="about-media">
          <img src="/media/products/basic-hoodie-big-yale.jpg" alt="A Campus Customs hoodie" />
          <blockquote>
            "If it's on the page, it's on the shelf." <cite>— the whole point of this site</cite>
          </blockquote>
        </Reveal>
      </div>
    </div>
  )
}
